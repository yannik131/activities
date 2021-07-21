from django.template.loader import render_to_string
from .models import User
from time import perf_counter_ns as timer
import datetime

def test():
    pks = [170, 180, 5, 19, 11, 9, 280, 24, 220, 230, 25, 3, 210, 20, 400, 31, 61, 390, 62, 63, 64, 16, 1, 650, 660, 67, 680, 2, 690, 60, 15]
    stamp = timer()
    for i in range(100):
        for u in pks:
            try:
                user = User.objects.get(pk=u)
            except User.DoesNotExist:
                user = None
    print((timer()-stamp)/10**6)
    stamp = timer()
    for i in range(100):
        for u in pks:
            user = User.objects.filter(pk=u)
            if user.exists():
                user = user.first()
            else:
                user = None
    print((timer()-stamp)/10**6)
    
def test7():
    stamp = timer()
    te = dict(a=1, b=2, c=3, d=4, e=5)
    for i in range(1000):
        l = 'f' not in te
    print((timer()-stamp)/10**6)
    
def test8():
    stamp = timer()
    for i in range(1000):
        u = User.objects.get(pk=1)
        u.channel_name = 'None'
        u.save()
    print((timer()-stamp)/10**6)
    
    stamp = timer()
    for i in range(1000):
        u = User.objects.get(pk=1)
        u.channel_name = 'None'
        u.save(update_fields=['channel_name'])
    print((timer()-stamp)/10**6)
    
    stamp = timer()
    for i in range(1000):
        User.objects.only('channel_name').filter(pk=1).update(channel_name='None')
    print((timer()-stamp)/10**6)

def test9():
    u = User.objects.first()
    stamp = timer()
    for i in range(100):
        rooms = []
        rooms_with_news_count = 0
        chat_checks = u.last_chat_checks.prefetch_related('room', 'room__log_entries')
        newest_date = chat_checks.first().date
        for check in chat_checks:
            entry = check.room.log_entries.last()
            if entry and entry.created > newest_date:
                rooms_with_news_count += 1
            rooms.append((check.room, check.room.get_target(u), datetime.datetime.timestamp(entry.created) if entry else 0))
        rooms = sorted(rooms, key=lambda room: room[2], reverse=True)
        #chat_list = render_to_string('chat/chat_list.html', dict(rooms=rooms, rooms_with_news_count=rooms_with_news_count))
    print((timer()-stamp)/10**6)
    
    
def test10():
    pks = list(User.objects.values_list('id', flat=True))
    stamp = timer()
    for i in range(100):
        for u in pks:
            try:
                user = User.objects.get(pk=u)
            except User.DoesNotExist:
                user = None
    print((timer()-stamp)/10**6)
    stamp = timer()
    for i in range(100):
        for u in pks:
            user = User.objects.get(pk=u)
    print((timer()-stamp)/10**6)

def test11():
    pks = list(User.objects.values_list('id', flat=True))
    arr = [2, 5, 1, 2, 6, 3, 6, 8, 4, 1, 6, 8, 4]
    stamp = timer()
    for i in range(10**6):
        try:
            arr = sorted(arr)
        except:
            pass
    print((timer()-stamp)/10**6)
    stamp = timer()
    for i in range(10**6):
        arr = sorted(arr)
    print((timer()-stamp)/10**6)
