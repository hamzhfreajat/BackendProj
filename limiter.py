from slowapi import Limiter
from auth import get_real_ip

def get_ipaddr(request):
    return get_real_ip(request)

limiter = Limiter(key_func=get_ipaddr)
