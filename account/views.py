from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.db import models
from django.http.response import HttpResponse, HttpResponseForbidden
from character.models import Suggestion
from django.core.mail import message
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import GuestForm, LocationForm, UserRegistrationForm, UserEditForm, FriendRequestForm, CustomFriendRequestForm, DeleteForm, LoginForm
from .models import FriendRequest, LocationMarker, User, Friendship, Location
from django.http import HttpResponseRedirect
from django.utils import timezone
from datetime import timedelta
from .templatetags import account_tags
from notify.utils import notify
from wall.models import Post
from shared import shared
from .utils import send_account_activation_email, send_mail
from activities.language_subdomain_middleware import get_prefix
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_text
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.urls import reverse
from django.db.models import Q
from django.contrib.auth.validators import UnicodeUsernameValidator
#validator = UnicodeUsernameValidator()
import logging
logger = logging.getLogger('django')
import random


@login_required
def home(request):
    missing_fields = request.user.birth_year is None or request.user.sex is None
    return render(request, 'account/home.html', dict(missing_fields=missing_fields))


def check_username(request, username):
    try:
        #validator(username)
        User.objects.get(username=username)
        return HttpResponseForbidden('exists')
    #except ValidationError:
    #    return HttpResponseForbidden('invalid')
    except User.DoesNotExist:
        return HttpResponse()

def about(request):
    return render(request, 'account/about.html', dict(prefix=get_prefix(request)))


@login_required
def user_post_list(request):
    posts, page = Post.get_page(request)
    return render(request, 'account/user_post_list.html', dict(posts=posts, page=page))


@login_required
def detail(request, username):
    user = get_object_or_404(User, username=username)
    if request.user == user:
        return HttpResponseRedirect(request.build_absolute_uri('/account/'))
    requested = FriendRequest.objects.filter(requesting_user=request.user, requested_user=user).exists()
    friendship = request.user.get_friendship_for(user)
    posts = Post.get_approved_posts_for(user)
    posts, page = shared.paginate(posts, request)
    if request.user.character and user.character:
        score = request.user.character.congruence_with(user.character)
    else:
        score = None
    return render(request, 'account/detail.html', {'viewed_user': user, 'friendship': friendship, 'requested': requested, 'posts': posts, 'score': score, 'age': user.age, 'sex': user.get_sex_display()})


@login_required
def send_friend_request(request, target_id):
    requested_user = get_object_or_404(User, id=target_id)
    if FriendRequest.objects.filter(requesting_user=request.user, requested_user=requested_user).exists():
        messages.add_message(request, messages.INFO, _('Sie haben diesem Nutzer bereits früher eine Freundschaftsanfrage gesendet. Solange diese nicht von ihm gelöscht wird, können Sie keine weitere Anfrage senden.'))
        return HttpResponseRedirect(requested_user.get_absolute_url())
    elif Friendship.objects.filter(Q(to_user=request.user, from_user=requested_user) | Q(to_user=requested_user, from_user=request.user)).exists():
        messages.add_message(request, messages.INFO, _('Ihr seid bereits Freunde.'))
        return HttpResponseRedirect(requested_user.get_absolute_url())
    if request.method == 'POST':
        form = FriendRequestForm(request.POST)
        if form.is_valid():
            message = form.cleaned_data['message']
            FriendRequest.objects.create(requesting_user=request.user, requested_user=requested_user, request_message=message)
            messages.add_message(request, messages.INFO, _('Freundschaftsanfrage wurde verschickt.'))
            return HttpResponseRedirect(requested_user.get_absolute_url())
    else:
        form = FriendRequestForm()
    return render(request, 'account/send_friend_request.html', {'form': form, 'target_user': requested_user})


@login_required
def send_custom_friend_request(request):
    if request.method == 'POST':
        form = CustomFriendRequestForm(request.POST)
        if form.is_valid():
            message = form.cleaned_data['message']
            user = User.objects.get(username=form.cleaned_data['username'])
            if user == request.user:
                messages.add_message(request, messages.INFO, _('Sie können sich nicht selbst eine Freundschaftsanfrage schicken.'))
                return HttpResponseRedirect(request.build_absolute_uri('/account/friend_requests_list/'))
            elif Friendship.objects.filter(Q(to_user=request.user, from_user=user) | Q(to_user=user, from_user=request.user)).exists():
                messages.add_message(request, messages.INFO, _('Ihr seid bereits Freunde.'))
                return HttpResponseRedirect(request.build_absolute_uri('/account/friend_requests_list/'))
            fr, created = FriendRequest.objects.get_or_create(requesting_user=request.user, requested_user=user, request_message=message)
            if not created:
                fr.request_message = message
                fr.save()
            return HttpResponseRedirect(request.build_absolute_uri('/account/friend_requests_list/'))
    else:
        form = CustomFriendRequestForm()
    return render(request, 'account/send_friend_request.html', dict(form=form))


@login_required
def accept_request(request, id):
    friend_request = get_object_or_404(FriendRequest, requested_user=request.user, id=id)
    if Friendship.objects.filter(Q(to_user=request.user, from_user=friend_request.requesting_user) | Q(to_user=friend_request.requesting_user, from_user=request.user)).exists():
        messages.add_message(request, messages.INFO, _('Ihr seid bereits Freunde.'))
    else:
        friendship, created = Friendship.objects.get_or_create(from_user=friend_request.requesting_user, to_user=friend_request.requested_user)
    friend_request.delete()
    return HttpResponseRedirect(request.build_absolute_uri('/account/friend_requests_list/'))


@login_required
def decline_request(request, id):
    friend_request = get_object_or_404(FriendRequest, requested_user=request.user, id=id)
    friend_request.set_status('declined')
    notify(friend_request.requesting_user, request.user, 'declined_friend_request', url=friend_request.get_absolute_url())
    return HttpResponseRedirect(request.build_absolute_uri('/account/friend_requests_list/'))


@login_required
def delete_request(request, id):
    friend_request = get_object_or_404(FriendRequest, id=id)
    if (friend_request.requesting_user == request.user and friend_request.status != 'declined') or (friend_request.requested_user == request.user and friend_request.status != 'pending'):
        FriendRequest.objects.filter(id=id).delete()
    else:
        messages.add_message(request, messages.INFO, _('Sie können diese Anfrage nicht löschen.'))
    return HttpResponseRedirect(request.build_absolute_uri('/account/friend_requests_list/'))


@login_required
def friend_requests_list(request):
    sent_friend_requests = request.user.sent_friend_requests.all()
    received_friend_requests = request.user.received_friend_requests.all()
    changed_requests = account_tags.changed_requests(request.user)
    request.user.latest_request_check = timezone.now()
    request.user.save()
    return render(request, 'account/friend_requests_list.html', dict(sent_friend_requests=sent_friend_requests, received_friend_requests=received_friend_requests, changed_requests=changed_requests))


@login_required
def destroy_friendship(request, id):
    user = get_object_or_404(User, id=id)
    friendship = user.get_friendship_for(request.user)
    if friendship:
        friendship.delete()
    else:
        messages.add_message(request, messages.INFO, _('Diese Freundschaft existiert nicht mehr.'))
        return HttpResponseRedirect(request.build_absolute_uri('/account/friend_requests_list/'))
    if request.user == friendship.to_user:
        recipient = friendship.from_user
    else:
        recipient = friendship.to_user
    notify(recipient, request.user, 'terminated_friendship')
    messages.add_message(request, messages.INFO, _('Sie haben die Freundschaft mit {user} beendet.').format(user=user))
    return HttpResponseRedirect(user.get_absolute_url())


def register(request):
    if request.user.is_authenticated and not request.user.is_guest:
        return HttpResponseRedirect(reverse('account:home'))
    if request.method == 'POST':
        location_form = LocationForm(request.POST)
        user_form = UserRegistrationForm(request.POST, files=request.FILES)
        if user_form.is_valid():
            if location_form.is_valid():
                if isinstance(request.user, AnonymousUser):
                    user = user_form.save(commit=False)
                else:
                    cd = user_form.cleaned_data
                    user = request.user
                    user.username = cd['username']
                    user.email = cd['email']
                    user.sex = cd.get('sex')
                    user.birth_year = cd.get('birth_year')
                    user.image = cd.get('image')
                    user.is_guest = False
                    auth_logout(request)
                user.set_password(user_form.cleaned_data['password'])
                user.location = location_form.location
                user.is_active = False
                user.save()
                try:
                    send_account_activation_email(request, user)
                except Exception as e:
                    logger.log(logging.ERROR, 'Could not send activation e-mail', exc_info=True)
                    user.delete()
                    messages.add_message(request, messages.INFO, _('An die E-Mail Adresse konnte keine E-Mail gesendet werden.'))
                    return render(request, 'registration/register.html', {'user_form': user_form, 'location_form': location_form})
                return render(request, 'registration/register_done.html', {'new_user': user})
    else:
        user_form = UserRegistrationForm()
        location_form = LocationForm()
    return render(request, 'registration/register.html', {'user_form': user_form, 'location_form': location_form})


@login_required
def edit(request):
    if request.user.is_guest:
        messages.add_message(request, messages.INFO, _('Sie müssen sich vorher registrieren, wenn Sie Ihren Account bearbeiten wollen.'))
        return HttpResponseRedirect(reverse('account:register'))
    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user, data=request.POST, files=request.FILES)
        if user_form.is_valid():
            user_form.save()
            messages.add_message(request, messages.INFO, _('Änderungen gespeichert.'))
    else:
        user_form = UserEditForm(instance=request.user)
    change_location_date = None
    if request.user.last_location_change:
        change_location_date = request.user.last_location_change+timedelta(days=User.LOCATION_CHANGE_DAYS)
        if change_location_date < timezone.now():
            change_location_date = None
    return render(request, 'account/edit.html', {'user_form': user_form, 'location': request.user.location.as_dict(), 'change_location_date': change_location_date})


@login_required
def edit_address(request):
    if request.user.is_guest:
        messages.add_message(request, messages.INFO, _('Sie müssen sich vorher registrieren, wenn Sie Ihren Ort ändern wollen.'))
        return HttpResponseRedirect(reverse('account:register'))
    if request.user.last_location_change and (timezone.now() < request.user.last_location_change+timedelta(days=User.LOCATION_CHANGE_DAYS)):
        messages.add_message(request, messages.INFO, _('Sie können den Ort nur höchstens alle 7 Tage wechseln.'))
        return HttpResponseRedirect(reverse('account:edit'))
    if request.method == 'POST':
        location_form = LocationForm(request.POST)
        if location_form.is_valid():
            request.user.location = Location.determine_from(location_form.cleaned_data['address'])
            request.user.last_location_change = timezone.now()
            request.user.save()
            messages.add_message(request, messages.INFO, _('Neue Adresse gespeichert: ')+request.user.location.full_address())
            return HttpResponseRedirect(reverse('account:edit'))
    else:
        location_form = LocationForm()
    return render(request, 'account/edit_address.html', {'location_form': location_form})


@login_required
def view_friendship(request, id):
    friendship = get_object_or_404(Friendship, id=id)
    if friendship.to_user == request.user:
        return HttpResponseRedirect(friendship.from_user.get_absolute_url())
    return HttpResponseRedirect(friendship.to_user.get_absolute_url())
    

def delete(request):
    if request.method == 'POST':
        delete_form = DeleteForm(request.POST)
        if delete_form.is_valid():
            try:
                request.user.delete()
            except models.ProtectedError:
                messages.add_message(request, messages.INFO, _('Sie sind noch Admin mindestens einer Gruppe. Löschen sie zuerst diese Gruppen oder legen Sie einen neuen Admin fest, bevor Sie Ihren Account löschen.'))
                return HttpResponseRedirect(reverse('usergroups:group_list'))
            Suggestion.objects.filter(character__user__id=request.user.id).delete()
            send_mail(f'Delete: {request.user}. Total: {User.objects.count()-1}')
            return HttpResponseRedirect(reverse('account:home'))
    else:
        delete_form = DeleteForm()
    return render(request, 'account/delete.html', dict(delete_form=delete_form))
    

def activate(request, uidb64=None, token=None):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except User.DoesNotExist:
        user = None
    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        auth_login(request, user)
        send_mail(f'Registration {User.objects.count()}: {user}', f'Location: {user.location}, Inactive: {User.objects.filter(is_active=False).count()}')
        return HttpResponseRedirect(reverse('account:home'))
    else:
        messages.add_message(request, messages.INFO, _('Der Aktivierungslink ist ungültig. Falls der Account noch inaktiv ist, können Sie durch erneutes Registrieren einen neuen anfordern!'))
        return HttpResponseRedirect(reverse('account:register'))


def guest_access(request):
    if request.user.is_authenticated:
        messages.add_message(request, messages.INFO, _('Sie sind doch schon eingeloggt! Was wollen Sie denn noch!?'))
        return HttpResponseRedirect(reverse('account:home'))
    if request.method == 'POST':
        form = GuestForm(request.POST)
        if form.is_valid():
            city = 'Berlin'
            if request.LANGUAGE_CODE == 'en':
                city = 'Washington, D. C.'
            while True:
                username = _('Gast')+str(random.randint(1, 1000000))
                try:
                    user = User.objects.create(location=Location.determine_from(city), username=username, is_guest=True)
                    break
                except:
                    continue
            auth_login(request, user)
            return HttpResponseRedirect(reverse('account:home'))
    else:
        form = GuestForm()
    return render(request, 'registration/guest_access.html', dict(form=form, hours=int(User.GUEST_LIFESPAN.total_seconds()/3600)))


def login(request):
    if request.method == 'POST':
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            user = login_form.user
            auth_login(request, user)
            if request.POST.get('next'):
                return HttpResponseRedirect(request.build_absolute_uri(request.POST['next']))
            else:
                return HttpResponseRedirect(reverse('account:home'))
    else:
        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse('account:home'))
        login_form = LoginForm()
    return render(request, 'registration/login.html', dict(form=login_form, next=request.GET.get('next')))
    
def password_change_done(request):
    messages.add_message(request, messages.INFO, _('Passwort erfolgreich geändert.'))
    return HttpResponseRedirect(reverse('account:edit'))
    
def password_reset_complete(request):
    messages.add_message(request, messages.INFO, _('Ihr Passwort wurde zurückgesetzt.'))
    return HttpResponseRedirect(reverse('account:login'))
    
def people_list(request):
    component_index = int(request.GET.get('component_index', 3))
    search_string = request.GET.get('search_string')
    component = Location.components[component_index]
    chosen_component = getattr(request.user.location, component)
    location = request.user.location.get_parent(component_index)
    people = list()
    if search_string:
        users = User.objects.filter(username__icontains=search_string)
    else:
        users = location.get_population(User.objects.all()).exclude(id=request.user.id)
    method = request.GET.get('method', 'congruence')
    if method == 'congruence':
        for user in users[:100]:
            if user.character and request.user.character:
                people.append([user, request.user.character.congruence_with(user.character)])
            else:
                people.append([user, None])
        people = sorted(people, key=lambda t: t[1] if t[1] else 0, reverse=True)
    else:
        for user in users:
            people.append([user, request.user.activities.all() & user.activities.all()])
        people = sorted(people, key=lambda t: t[1].count() if t[1] else 0, reverse=True)
    people, page = shared.paginate(people, request, 10)
    return render(request, 'account/people_list.html', dict(people=people, component_index=component_index, chosen_component=chosen_component, location=location, search_string=search_string, method=method))
    
def delete_marker(request, marker_id):
    try:
        marker = LocationMarker.objects.get(pk=marker_id)
        marker.delete()
        messages.add_message(request, messages.INFO, _('Markierung wurde erfolgreich gelöscht.'))
    except:
        messages.add_message(request, messages.INFO, _('Markierung wurde nicht gefunden!'))
    return HttpResponseRedirect(reverse('account:edit'))
    
def impressum(request):
    return render(request, 'account/impressum.html')


def handler404(request, exception=None):
    return render(request, "account/404.html", dict())
    
    
def handler403(request, exception=None):
    return render(request, "account/403.html", dict())


def handler500(request):
    return render(request, "account/500.html",)