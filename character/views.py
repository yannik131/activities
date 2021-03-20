from django.shortcuts import render, get_object_or_404
from account.models import User
from .models import Character
from shared.shared import log
from activity.models import Activity, Category
from .utils import BIG_FIVE
import json
from django.http import HttpResponseForbidden, HttpResponseRedirect
from character.utils import create_trait_dict
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from shared.shared import paginate, log
from django.db.models.aggregates import Count


# Create your views here.
def overview(request, category_name=None):
    if not request.user.character:
        character = Character()
        character.save()
        request.user.character = character
        request.user.save()
    suggestions = None
    page = 0
    category = None
    if request.user.character.presentable:
        if category_name:
            category = Category.objects.get(translations__name=category_name, translations__language_code=request.LANGUAGE_CODE)
        else:
            category = Category.objects.get(translations__name="Freizeit", translations__language_code="de")
        suggestions = request.user.character.get_or_create_suggestions().filter(activity__in=category.activities.all())
        suggestions, page = paginate(suggestions, request, 6)
    return render(request, 'character/overview.html', dict(suggestions=suggestions, start=(int(page)-1)*6, categories=Category.objects.annotate(count=Count('activities')).filter(count__gt=0), chosen_category=category))
    

def quiz(request, limit=None):
    if not request.user.character.question_limit:
        if limit not in [60, 120, 240]:
            messages.add_message(request, messages.INFO, _('Wählen Sie zuerst einen der drei Fragebogen aus, bevor Sie beginnen.'))
            return HttpResponseRedirect(request.build_absolute_uri('/character/overview/'))
        request.user.character.question_limit = limit
        request.user.character.save()
    return render(request, 'character/quiz.html')
    
    
def reset_quiz(request):
    request.user.character.reset()
    return HttpResponseRedirect(request.build_absolute_uri('/character/overview/'))
    
    
def edit_weights(request, activity_id):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    activity = Activity.objects.get(pk=activity_id)
    next = Activity.objects.filter(pk__gt=activity.id).order_by('pk')
    if next.exists():
        next = next.first()
    else:
        next = None
    before = Activity.objects.filter(pk__lt=activity.id).order_by('-pk')
    if before.exists():
        before = before.first()
    else:
        before = None
    return render(request, 'character/edit_weights.html', dict(BIG_FIVE=BIG_FIVE, activity=activity, before=before, next=next))
    
