from django.core.mail import message
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import LocationForm, UserRegistrationForm, UserEditForm, FriendRequestForm, CustomFriendRequestForm, AccountDeleteForm, LoginForm
from .models import FriendRequest, LocationMarker, User, Friendship, Location
from django.http import HttpResponseRedirect
from django.utils import timezone
from datetime import timedelta
from .templatetags import account_tags
from notify.utils import notify
from wall.models import Post
from shared import shared
from .utils import send_account_activation_email
from activities.language_subdomain_middleware import get_prefix
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_text
from django.contrib.auth import login as auth_login
from django.urls import reverse
from django.db.models import Q
from django.core.mail import EmailMultiAlternatives
import logging
logger = logging.getLogger('django')


@login_required
def home(request):
    missing_fields = request.user.birth_year is None or request.user.sex is None
    return render(request, 'account/home.html', dict(missing_fields=missing_fields))


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
    posts = Post.objects.filter(author=user).all()
    posts, page = shared.paginate(posts, request)
    if request.user.character and user.character:
        score = request.user.character.congruence_with(user.character)
    else:
        score = None
    return render(request, 'account/detail.html', {'viewed_user': user, 'friendship': friendship, 'requested': requested, 'posts': posts, 'score': score})


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
    if request.user.is_authenticated:
        return HttpResponseRedirect(request.build_absolute_uri('/account'))
    if request.method == 'POST':
        location_form = LocationForm(request.POST)
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            if location_form.is_valid():
                new_user = user_form.save(commit=False)
                new_user.set_password(user_form.cleaned_data['password'])
                new_user.location = location_form.location
                new_user.is_active = False
                new_user.save()
                try:
                    send_account_activation_email(request, new_user)
                except Exception as e:
                    logger.log(logging.WARNING, 'Could not send activation e-mail', exc_info=True)
                    new_user.delete()
                    messages.add_message(request, messages.INFO, _('An die E-Mail Adresse konnte keine E-Mail gesendet werden.'))
                    return render(request, 'registration/register.html', {'user_form': user_form, 'location_form': location_form})
                return render(request, 'registration/register_done.html', {'new_user': new_user})
    else:
        user_form = UserRegistrationForm()
        location_form = LocationForm()
    return render(request, 'registration/register.html', {'user_form': user_form, 'location_form': location_form})

@login_required
def edit(request):
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
        delete_form = AccountDeleteForm(request.POST)
        if delete_form.is_valid():
            request.user.delete()
            return HttpResponseRedirect(request.build_absolute_uri('/'))
    else:
        delete_form = AccountDeleteForm()
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
        try:
            email = EmailMultiAlternatives(f'Registration {User.objects.count()}: {user}', f'Location: {user.location}, Inactive: {User.objects.filter(is_active=False).count()}', 'myactivities.net@web.de', ['yannik131@web.de'])
            email.send()
        except:
            logging.log(logging.ERROR, 'Could not send email', exc_info=True)
        return HttpResponseRedirect(request.build_absolute_uri('/'))
    else:
        messages.add_message(request, messages.INFO, _('Der Aktivierungslink ist ungültig. Falls der Account noch inaktiv ist, können Sie durch erneutes Registrieren einen neuen anfordern!'))
        return HttpResponseRedirect(reverse('account:register'))


def login(request):
    if request.method == 'POST':
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            user = login_form.user
            auth_login(request, user)
            return HttpResponseRedirect(request.build_absolute_uri('/'))
    else:
        if request.user.is_authenticated:
            return HttpResponseRedirect(request.build_absolute_uri('/'))
        login_form = LoginForm()
    return render(request, 'registration/login.html', dict(form=login_form))
    
def password_change_done(request):
    messages.add_message(request, messages.INFO, _('Passwort erfolgreich geändert.'))
    return HttpResponseRedirect(reverse('account:edit'))
    
def password_reset_complete(request):
    messages.add_message(request, messages.INFO, _('Ihr Passwort wurde zurückgesetzt.'))
    return HttpResponseRedirect(reverse('account:login'))
    
def people_list(request, search_string=None):
    component_index = int(request.GET.get('component_index', 3))
    component = Location.components[component_index]
    chosen_component = getattr(request.user.location, component)
    location = request.user.location.get_parent(component_index)
    people = list()
    if search_string:
        users = User.objects.filter(username__icontains=search_string)
    else:
        users = location.get_population(User.objects.all()).exclude(id=request.user.id)
    for user in users[:30]:
        if user.character and request.user.character:
            people.append([user, request.user.character.congruence_with(user.character)])
        else:
            people.append([user, None])
    people = sorted(people, key=lambda t: t[1] if t[1] else 0, reverse=True)
    people, page = shared.paginate(people, request, 10)
    return render(request, 'account/people_list.html', dict(people=people, component_index=component_index, chosen_component=chosen_component, location=location, search_string=search_string))
    
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