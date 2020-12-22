from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import LocationForm, UserRegistrationForm, UserEditForm, FriendRequestForm, CustomFriendRequestForm
from .models import Location, FriendRequest, User, Friendship
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.utils import timezone
from .templatetags import account_tags
from notify.utils import notify
from wall.models import Post
from shared import shared
from notify.models import Notification


@login_required
def home(request):
    return render(request, 'account/home.html')


def about(request):
    return render(request, 'account/about.html')


@login_required
def user_post_list(request):
    posts, page = Post.get_page(request)
    return render(request, 'account/user_post_list.html', dict(posts=posts, page=page))


@login_required
def detail(request, username):
    user = User.objects.get(username=username)
    if request.user == user:
        return HttpResponseRedirect(request.build_absolute_uri('/account/edit/'))
    requested = False
    if FriendRequest.objects.filter(requesting_user=request.user, requested_user=user).exists():
        requested = True
    friendship = request.user.get_friendship_for(user)
    posts = Post.objects.filter(author=user, target_ct=User.content_type(), target_id=user.id).all()
    return render(request, 'account/detail.html', {'viewed_user': user, 'friendship': friendship, 'requested': requested, 'posts': posts})


@login_required
def send_friend_request(request, target_id):
    sent = False
    requested_user = User.objects.get(id=target_id)
    if FriendRequest.objects.filter(requesting_user=request.user, requested_user=requested_user).exists():
        return HttpResponse(
            'Sie haben diesem Nutzer bereits früher eine Freundschaftsanfrage gesendet. Solange diese nicht von ihm gelöscht wird, können Sie keine weitere Anfrage senden.')
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
                return HttpResponse(
                'Haha. Sehr lustig. Hast du nichts besseres zu tun als zu gucken ob das funktioniert? Nein? Ich auch nicht...')
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
    friend_request = FriendRequest.objects.get(id=id)
    if (friend_request.requesting_user == request.user and friend_request.status != 'declined') or (friend_request.requested_user == request.user and friend_request.status != 'pending'):
        FriendRequest.objects.filter(id=id).delete()
    else:
        return HttpResponse('Nö.')
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
    user = User.objects.get(id=id)
    friendship = user.get_friendship_for(request.user)
    if friendship:
        friendship.delete()
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
            new_user.location = shared.get_location(location_form.cleaned_data['address'])
            new_user.save()
            return render(request, 'account/register_done.html', {'new_user': new_user})
    else:
        user_form = UserRegistrationForm()
        location_form = LocationForm()
    return render(request, 'account/register.html', {'user_form': user_form, 'location_form': location_form})


@login_required
def edit(request):
    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user, data=request.POST, files=request.FILES)
        if user_form.is_valid():
            user_form.save()
    else:
        user_form = UserEditForm(instance=request.user)
    return render(request, 'account/edit.html', {'user_form': user_form, 'location': request.user.location.as_dict()})


@login_required
def edit_address(request):
    sent = False
    if request.method == 'POST':
        location_form = LocationForm(request.POST)
        if location_form.is_valid():
            request.user.location = shared.get_location(location_form.cleaned_data['address'])
            request.user.save()
            sent = True
    else:
        location_form = LocationForm()
    return render(request, 'account/edit_address.html', {'location_form': location_form, 'sent': sent})


@login_required
def view_friendship(request, id):
    friendship = Friendship.objects.get(id=id)
    if friendship.to_user == request.user:
        return HttpResponseRedirect(friendship.from_user.get_absolute_url())
    return HttpResponseRedirect(friendship.to_user.get_absolute_url())
