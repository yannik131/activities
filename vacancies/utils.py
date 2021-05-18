from .models import Vacancy, Invitation

def clear_vacancies_for(instance):
    target_ct = type(instance).content_type()
    Invitation.objects.filter(target_ct=target_ct, target_id=instance.id).delete()
    Vacancy.objects.filter(target_ct=target_ct, target_id=instance.id).delete()