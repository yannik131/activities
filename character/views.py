from django.shortcuts import render, get_object_or_404
from account.models import User
from .models import Character
from shared.shared import log
from .models import BIG_FIVE

# Create your views here.
def overview(request):
    if not request.user.character:
        character = Character()
        character.save()
        request.user.character = character
        request.user.save()
    return render(request, 'character/overview.html')
    

def quiz(request):
    return render(request, 'character/quiz.html')
    
    
def reset_quiz(request):
    request.user.character.init_traits()
    request.user.character.current_question = 0
    request.user.character.save()
    return render(request, 'character/overview.html')