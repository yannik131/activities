from .models import User
from time import perf_counter_ns as timer

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
    
def test5():
    stamp = timer()
    for i in range(1000):
        u = User.objects.get(pk=1)
        u.channel_name = 'None'
        u.save()
    print((timer()-stamp)/10**6)
    stamp = timer()
    for i in range(1000):
        User.objects.only('channel_name').filter(pk=1).update(channel_name='None')
    print((timer()-stamp)/10**6)
