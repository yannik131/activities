from django.shortcuts import render, get_object_or_404
from .forms import PostForm, CommentForm
from django.http import HttpResponseRedirect
from .models import Post, Comment
from account.models import User
from usergroups.models import UserGroup
from activity.models import Category
from django.contrib.contenttypes.models import ContentType
from shared.shared import slashify
from account.views import handler403


def create_post(request, app_label, model, id):
    ct = get_object_or_404(ContentType, app_label=app_label, model=model)
    arg = ct.get_object_for_this_type(pk=id)
    if request.method == 'POST':
        form = PostForm(arg, request.LANGUAGE_CODE, data=request.POST, files=request.FILES)
        form.instance.target_ct = ct
        form.instance.target_id = id
        form.instance.author = request.user
        if form.is_valid():
            post = form.save()
            if ct == User.content_type():
                return HttpResponseRedirect(request.build_absolute_uri('/account/user_post_list/'))
            return HttpResponseRedirect(post.target.get_absolute_url())
    else:
        form = PostForm(arg, request.LANGUAGE_CODE)
        form.instance.target_ct = ct
        form.instance.target_id = id
    return render(request, 'wall/post/create_post.html', dict(form=form, target=form.instance.target))


def delete_post(request, id, path):
    post = get_object_or_404(Post, id=id) 
    if request.user == post.author:
        post.delete()
        return HttpResponseRedirect(request.build_absolute_uri(slashify(path)))
    return handler403(request)


def create_comment(request, id, path):
    post = get_object_or_404(Post, id=id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            return HttpResponseRedirect(request.build_absolute_uri(slashify(path)))
    else:
        form = CommentForm()
    return render(request, 'wall/post/create_comment.html', dict(form=form))


def delete_comment(request, id, path):
    comment = get_object_or_404(Comment, id=id)
    if comment.author == request.user:
        comment.delete()
        return HttpResponseRedirect(request.build_absolute_uri(slashify(path)))
    return handler403(request)
    