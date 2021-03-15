from django.shortcuts import render, get_object_or_404
from account.models import User
from .models import Character
from shared.shared import log
from activity.models import Activity
from .utils import BIG_FIVE
import json
from django.http import HttpResponseForbidden


# Create your views here.
def overview(request):
    if not request.user.character:
        character = Character()
        character.save()
        request.user.character = character
        request.user.save()
    if request.user.character.current_question == 120:
        request.user.character.activity_suggestions.all().delete()
        request.user.character.calculate_suggestions()
    return render(request, 'character/overview.html')
    

def quiz(request):
    return render(request, 'character/quiz.html')
    
    
def reset_quiz(request):
    request.user.character.init_traits()
    request.user.character.current_question = 0
    request.user.character.save()
    return render(request, 'character/overview.html')
    
    
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
    
