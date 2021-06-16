from django.db import models
from account.models import User, Location
from activity.models import Activity, Category
from usergroups.models import UserGroup
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from shared.shared import paginate
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    group = models.ForeignKey(UserGroup, on_delete=models.SET_NULL, related_name='posts', blank=True, null=True)
    target_ct = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    target_id = models.PositiveIntegerField(db_index=True)
    target = GenericForeignKey('target_ct', 'target_id')
    message = models.TextField()
    created = models.DateTimeField(default=now)
    audio = models.FileField(upload_to='audio/%Y/%m/%d/', null=True, blank=True)
    video = models.FileField(upload_to='video/%Y/%m/%d/', null=True, blank=True)
    image = models.FileField(upload_to='images/%Y/%m/%d/', null=True, blank=True)
    media_mime_type = models.CharField(max_length=50, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='posts')
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='posts', null=True, blank=True)
    liked_by = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    disliked_by = models.ManyToManyField(User, related_name='disliked_posts', blank=True)
    approved = models.BooleanField(default=False)

    class Meta:
        ordering = ('-created',)
        
    @property
    def contains_media(self):
        return any(tag in self.message for tag in ['<img', '<audio', '<video', '<a']) or self.media_mime_type
        
    @staticmethod
    def get_approved_posts_for(object):
        return object.posts.filter(approved=True)

    @staticmethod
    def get_page(request, component_index=None, chosen_component=None, activity=None, category=None):
        if component_index is None:
            object_list = Post.get_approved_posts_for(request.user)
        else:
            if activity is not None:
                post_list = Post.get_approved_posts_for(activity)
            else:
                post_list = Post.get_approved_posts_for(category)
            if component_index == 3:
                object_list = post_list.filter(author__location__city=chosen_component)
            elif component_index == 2:
                object_list = post_list.filter(author__location__county=chosen_component)
            elif component_index == 1:
                object_list = post_list.filter(author__location__state=chosen_component)
            else:
                object_list = post_list.filter(author__location__country=chosen_component)
        return paginate(object_list, request)
        
    def __str__(self):
        return _('Post vom ') + str(self.created)
        
    def verbose(self):
        if len(self.message) > 0:
            return self.message[:10]+".."
        return self.__str__()
        
    def get_absolute_url(self):
        return self.target.get_absolute_url()


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    message = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    created = models.DateTimeField(auto_now_add=True)
    users_liked = models.ManyToManyField(User, related_name='liked_comments')
