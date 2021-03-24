from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import LocationForm, UserRegistrationForm, UserEditForm, FriendRequestForm, CustomFriendRequestForm, AccountDeleteForm, LoginForm
from .models import Location, FriendRequest, User, Friendship
from django.http import HttpResponseRedirect
from django.utils import timezone
from .templatetags import account_tags
from notify.utils import notify
from wall.models import Post
from shared import shared
from .utils import get_location
from activities.language_subdomain_middleware import get_prefix
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_text
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.auth import login as auth_login


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
        return HttpResponseRedirect(request.build_absolute_uri('/account/edit/'))
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
    sent = False
    requested_user = get_object_or_404(User, id=target_id)
    if FriendRequest.objects.filter(requesting_user=request.user, requested_user=requested_user).exists():
        messages.add_message(request, messages.INFO, _('Sie haben diesem Nutzer bereits früher eine Freundschaftsanfrage gesendet. Solange diese nicht von ihm gelöscht wird, können Sie keine weitere Anfrage senden.'))
        return HttpResponseRedirect(requested_user.get_absolute_url())
    if request.method == 'POST':
        form = FriendRequestForm(request.POST)
        if form.is_valid():
            message = form.cleaned_data['message']
            FriendRequest.objects.create(requesting_user=request.user, requested_user=requested_user, request_message=message)
            sent = True
    else:
        form = FriendRequestForm()
    return render(request, 'account/send_friend_request.html', {'form': form, 'sent': sent, 'target_user': requested_user})


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
    _, created = Friendship.objects.get_or_create(from_user=friend_request.requesting_user, to_user=friend_request.requested_user)
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
    return render(request, 'account/destroy_friendship.html', {'target_user': user})


def register(request):
    if request.method == 'POST':
        location_form = LocationForm(request.POST)
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid() and location_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.set_password(user_form.cleaned_data['password'])
            new_user.location = get_location(location_form.cleaned_data['address'])
            new_user.is_active = False
            new_user.save()
            send_account_activation_email(request, new_user)
            return render(request, 'account/register_done.html', {'new_user': new_user})
    else:
        user_form = UserRegistrationForm(initial=dict(birth_year=1990))
        location_form = LocationForm()
    return render(request, 'account/register.html', {'user_form': user_form, 'location_form': location_form})


@login_required
def edit(request):
    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user, data=request.POST, files=request.FILES)
        if user_form.is_valid():
            user_form.save()
            messages.add_message(request, messages.INFO, _('Änderungen gespeichert.'))
    else:
        user_form = UserEditForm(instance=request.user)
    return render(request, 'account/edit.html', {'user_form': user_form, 'location': request.user.location.as_dict()})


@login_required
def edit_address(request):
    sent = False
    if request.method == 'POST':
        location_form = LocationForm(request.POST)
        if location_form.is_valid():
            request.user.location = get_location(location_form.cleaned_data['address'])
            request.user.save()
            sent = True
    else:
        location_form = LocationForm()
    return render(request, 'account/edit_address.html', {'location_form': location_form, 'sent': sent})


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
    
def send_account_activation_email(request, user):
    from_email = settings.DEFAULT_FROM_EMAIL
    recipients = [user.email]
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    activation_url = request.build_absolute_uri(f'/account/activate/{uidb64}/{token}/')
    html_content = render_to_string('registration/activation_email.html', dict(user=user, activation_url=activation_url))
    email = EmailMultiAlternatives(_('E-Mail Aktivierung'), _('Aktivierungs-E-Mail'), settings.DEFAULT_FROM_EMAIL, recipients)
    email.attach_alternative(html_content, 'text/html')
    email.send()
    

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
        return HttpResponseRedirect(request.build_absolute_uri('/'))
    else:
        return HttpResponseRedirect(request.build_absolute_uri('/account/activation_failed/'))
        
def activation_failed(request):
    return render(request, 'registration/activation_failed.html')


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
    
    
def people_list(request):
    people = list()
    for user in request.user.location.population.exclude(id=request.user.id):
        if user.character and request.user.character:
            people.append([user, request.user.character.congruence_with(user.character)])
        else:
            people.append([user, None])
    people = sorted(people, key=lambda t: t[1] if t[1] else 0, reverse=True)
    people, page = shared.paginate(people, request, 12)
    return render(request, 'account/people_list.html', dict(people=people))
    
    
def impressum(request):
    return render(request, 'account/impressum.html')

def handler404(request, exception=None):
    return render(request, "account/404.html", dict())
    
    
def handler403(request, exception=None):
    return render(request, "account/403.html", dict())


def handler500(request):
    return render(request, "account/500.html")