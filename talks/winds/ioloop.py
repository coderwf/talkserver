# -*- coding:utf-8 -*-
"""
循环获取io事件并执行,全局单例模式
"""
import time
import bisect

#------------------------------------------------------------------------
_EPOLLIN = 0x001
_EPOLLPRI = 0x002
_EPOLLOUT = 0x004
_EPOLLERR = 0x008
_EPOLLHUP = 0x010
_EPOLLRDHUP = 0x2000
_EPOLLONESHOT = (1 << 30)
_EPOLLET = (1 << 31)

# Our events map exactly to the epoll events
NONE = 0
READ = _EPOLLIN
WRITE = _EPOLLOUT
ERROR = _EPOLLERR | _EPOLLHUP | _EPOLLRDHUP

"""
time.time()返回的是second
"""
class IoLoop(object):
    def __init__(self,poll_impl):
        self._poll_impl       = poll_impl
        self._handlers        = dict()
        self._events          = dict()

    @staticmethod
    def instance(cls,poll_impl):
        if not hasattr(cls,"_instance"):
            cls._instance = cls(poll_impl)
        return cls._instance

    def add_handler(self,fd,handler,events):
        fd , obj = self.split_fd(fd)
        if fd in self._handlers:
            raise IOError("fd {} already add ".format(fd))
        self._handlers[fd] = handler
        self._poll_impl.register(fd,events)

    def remove_handler(self,fd):
        fd , obj = self.split_fd(fd)
        self._handlers.pop(fd,None)
        self._poll_impl.unregister(fd)

    def modify_handler(self,fd,events):
        fd , obj = self.split_fd(fd)
        if fd not in self._handlers:
            raise IOError("fd {} not register ".format(fd))
        self._poll_impl.modify(fd,events)

    def start(self):
        while True:
            poll_timeout = 0.2
            events_pair = self._poll_impl.poll(poll_timeout)
            self._events.update(events_pair)
            while self._events:
                fd , events = self._events.popitem()
                handler     = self._handlers.get(fd)
                self._run_callback(handler,fd,events)

    def _run_callback(self,callback,*args,**kwargs):
        try:
            callback(*args,**kwargs)
        except Exception , e:
            print e

    def split_fd(self,fd):
        try:
            fd , obj = fd.fileno(),fd
        except:
            fd  , obj = fd , fd
        return fd,fd


class ExeLoop(object):
    def __init__(self):
        self.callbacks  = set()
        self.timeouts   = list()

    def exe_engine(self,callback):
        try:
            callback()
        except Exception , e :
            print e
            return

    def add_callback(self,callback):
        self.callbacks.add(callback)

    def add_timeout(self,deadline,callback):
        timeout = _Timeout(deadline,callback)
        bisect.insort(self.timeouts,timeout)
        return timeout

    def start(self):
        while True:
            callbacks = list(self.callbacks)
            for callback in callbacks:
                if callback in self.callbacks:
                    self.exe_engine(callback)
                    self.callbacks.remove(callback)
            if len(self.timeouts) > 0:
                now = time.time()
                while len(self.timeouts) >0 and self.timeouts[0].deadline <= now:
                    timeout = self.timeouts.pop(0)
                    self.exe_engine(timeout.callback)


#timeout是单次定时任务,只有当前时间大于等于deadline才会被执行
class _Timeout(object):
    __slots__ = ["callback","deadline"]
    def __init__(self,deadline,callback):
        self.callback = callback
        self.deadline = deadline

    def __cmp__(self, other):
        return cmp((self.deadline,id(self.callback)),
                   (other.deadline,id(other.callback)))


"""
callback is milliseconds (毫秒)
"""
class _PeriodTask(object):
    def __init__(self,callback,callback_time,exe_lopper):
        self.callback       = callback
        self.callback_time  = callback_time
        self._running       = False
        self._exe_lopper    = exe_lopper
        self.counter        = 0
    def stop(self):
        self._running = False

    def _run(self):
        if not self._running :
            return
        try:
            print self.counter
            self.counter += 1
            self.callback()
        except:
            pass
        self.start()

    def start(self):
        self._running = True
        deadline = time.time() + self.callback_time / 1000.0
        self._exe_lopper.add_timeout(deadline,self._run)

def f1():
    print "haha"

if __name__ == "__main__":
    lopper = ExeLoop()
    task = _PeriodTask(f1, 1000,lopper)
    task.start()
    lopper.start()
