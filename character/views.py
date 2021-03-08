from django.shortcuts import render, get_object_or_404
from account.models import User
from .models import Character
from shared.shared import log

# Create your views here.
def overview(request):
    if not request.user.character:
        character = Character()
        character.save()
        request.user.character = character
        request.user.save()
    return render(request, 'character/overview.html')