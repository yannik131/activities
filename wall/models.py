from django.db import models
from account.models import User, Location
from activity.models import Activity, Category
from usergroups.models import UserGroup
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from shared.shared import paginate


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    group = models.ForeignKey(UserGroup, on_delete=models.SET_NULL, related_name='posts', blank=True, null=True)
    target_ct = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    target_id = models.PositiveIntegerField(db_index=True)
    target = GenericForeignKey('target_ct', 'target_id')
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    audio = models.FileField(upload_to='audio/%Y/%m/%d/', null=True, blank=True)
    video = models.FileField(upload_to='video/%Y/%m/%d/', null=True, blank=True)
    image = models.FileField(upload_to='images/%Y/%m/%d/', null=True, blank=True)
    media_mime_type = models.CharField(max_length=50, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='posts')
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='posts', null=True, blank=True)
    users_liked = models.ManyToManyField(User, related_name='liked_posts')

    class Meta:
        ordering = ('-created',)

    @staticmethod
    def get_page(request, component_index=None, activity=None, category=None):
        object_list = []
        if component_index is None:
            object_list = Post.objects.filter(author=request.user, target_id=request.user.id, target_ct=User.content_type()).all()
        else:
            if activity is not None:
                post_list = Post.objects.filter(activity=activity)
            elif category is not None:
                post_list = Post.objects.filter(category=category)
            for post in post_list:
                if request.user.location.equal_to(post.author.location, Location.components[component_index]):
                    object_list.append(post)
        return paginate(object_list, request)


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    message = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    created = models.DateTimeField(auto_now_add=True)
    users_liked = models.ManyToManyField(User, related_name='liked_comments')
