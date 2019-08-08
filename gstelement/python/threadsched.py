from ctypes import *
import errno

SCHED_OTHER = 0
SCHED_FIFO = 1
SCHED_RR = 2


class SCHED_PARAM(Structure):
    _fields_ = [("prio", c_int)]


try:
    __pthread = CDLL("libpthread.so")
except OSError:
    # Ubuntu being silly
    import sysconfig
    import os
    arch = sysconfig.get_config_var("MULTIARCH")
    __pthread = CDLL(os.path.join("/lib/", arch, "libpthread.so.0"))

__pthread.pthread_self.restype = c_void_p
__pthread.pthread_getschedparam.argtypes = [c_void_p, POINTER(c_int), POINTER(SCHED_PARAM)]
__pthread.pthread_getschedparam.restype = c_int
__pthread.pthread_setschedparam.argtypes = [c_void_p, c_int, POINTER(SCHED_PARAM)]
__pthread.pthread_setschedparam.restype = c_int


def get_curschedparam():
    "Get scheduler parameters of running thread"
    policy = c_int()
    param = SCHED_PARAM()
    __pthread.pthread_getschedparam(__pthread.pthread_self(), byref(policy), byref(param))
    return policy.value, param.prio


def set_curschedparam(policy, prio):
    "Set scheduler parameters of running thread"
    param = SCHED_PARAM()
    param.prio = prio
    ret = __pthread.pthread_setschedparam(__pthread.pthread_self(), policy, byref(param))

    if ret == errno.EPERM:
        raise PermissionError

    return ret

def get_curthreadid():
    "Get current running thread id"
    return __pthread.pthread_self()
