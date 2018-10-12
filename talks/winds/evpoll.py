# -*- coding:utf-8 -*-

import select
import ioloop
"""
select.epoll()  无需再次封装
select.kqueue()
select.select()
"""
class _Select(object):
    def __init__(self):
        self.fd_reads     = set()
        self.fd_writes    = set()
        self.fd_errors    = set()
        self.fd_sets      = (self.fd_reads,self.fd_writes,self.fd_errors)

    def register(self,fd,events):
        if fd in self.fd_reads or fd in self.fd_writes or fd in self.fd_errors:
            raise IOError("fd {} already registered".format(fd))
        if events & ioloop.READ:
            self.fd_reads.add(fd)
        if events & ioloop.WRITE:
            self.fd_writes.add(fd)
        if events & ioloop.ERROR:
            self.fd_errors.add(fd)

    def unregister(self,fd):
        self.fd_errors.discard(fd)
        self.fd_writes.discard(fd)
        self.fd_reads.discard(fd)

    def modify(self,fd,events):
        self.unregister(fd)
        self.register(fd,events)

    def close(self):
        pass

    def poll(self,timeout):
        reads,writes,errors = select.select(self.fd_reads,self.fd_writes,self.fd_errors,timeout)
        events = dict()
        for fd in reads:
            events[fd] = events.get(fd,0) | ioloop.READ
        for fd in writes:
            events[fd] = events.get(fd,0) | ioloop.WRITE
        for fd in errors:
            events[fd] = events.get(fd, 0) | ioloop.ERROR
        return events.items()   # [(),(),()]


class _KQueue(object):
    """A kqueue-based event loop for BSD/Mac systems."""
    def __init__(self):
        self._kqueue = select.kqueue()
        self._active = {}

    def fileno(self):
        return self._kqueue.fileno()

    def close(self):
        self._kqueue.close()

    def register(self, fd, events):
        if fd in self._active:
            raise IOError("fd %s already registered" % fd)
        self._control(fd, events, select.KQ_EV_ADD)
        self._active[fd] = events

    def modify(self, fd, events):
        self.unregister(fd)
        self.register(fd, events)

    def unregister(self, fd):
        events = self._active.pop(fd)
        self._control(fd, events, select.KQ_EV_DELETE)

    def _control(self, fd, events, flags):
        kevents = []
        if events & ioloop.WRITE:
            kevents.append(select.kevent(
                fd, filter=select.KQ_FILTER_WRITE, flags=flags))
        if events & ioloop.READ:
            kevents.append(select.kevent(
                fd, filter=select.KQ_FILTER_READ, flags=flags))
        # Even though control() takes a list, it seems to return EINVAL
        # on Mac OS X (10.6) when there is more than one event in the list.
        for kevent in kevents:
            self._kqueue.control([kevent], 0)

    def poll(self, timeout):
        kevents = self._kqueue.control(None, 1000, timeout)
        events = {}
        for kevent in kevents:
            fd = kevent.ident
            if kevent.filter == select.KQ_FILTER_READ:
                events[fd] = events.get(fd, 0) | ioloop.READ
            if kevent.filter == select.KQ_FILTER_WRITE:
                if kevent.flags & select.KQ_EV_EOF:
                    events[fd] = ioloop.ERROR
                else:
                    events[fd] = events.get(fd, 0) | ioloop.WRITE
            if kevent.flags & select.KQ_EV_ERROR:
                events[fd] = events.get(fd, 0) | ioloop.ERROR
        return events.items()


if hasattr(select,"epoll"):
    _epoll = select.epoll
elif hasattr(select,"kqueue"):
    _epoll = _KQueue
else:
    print "fall back to select"
    _epoll = _Select
