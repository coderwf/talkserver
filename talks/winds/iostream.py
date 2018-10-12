# -*- coding:utf-8 -*-

import socket
import ioloop
import errno
"""
只有在需要的时候才将需要监听的事件进行注册

"""
class IoStream(object):  # 10M 4KB
    def __init__(self,sock,iolooper,max_buffer_size=10485760,read_chunk_size=4096):
        self._sock                    = sock
        self._iolooper                = iolooper
        self.max_buffer_size          = max_buffer_size
        self.read_chunk_size          = read_chunk_size
        self.read_delimiter           = None
        self.read_num_bytes           = None
        self._read_callback           = None
        self._write_callback          = None
        self._read_buffer             = ""
        self._write_buffer            = ""
        self._close_callback          = None
        self._state                   = ioloop.ERROR
        #初始只需要监听error事件
        self._sock.setblocking(False)
        self._iolooper.add_handler(self._sock,self._events_handler,self._state)

    #handle完了以后需要更新需要监听的io事件
    #需要监听什么就注册什么,如果在read或者write完成以后没有需要监听的读写,则只需要监听error即可
    def _events_handler(self,fd,events):
        if not self._sock :
            print "got events from closed stream"
            return
        if events & ioloop.READ:
            self._handle_read()
        if not self._sock :
            return
        if events & ioloop.WRITE:
            self._handle_write()
        if not self._sock :
            return
        if events & ioloop.ERROR: #发生了io错误则直接关闭流
            self.close()
            return
        state = ioloop.ERROR
        if self.read_delimiter or self.read_num_bytes:
            state |= ioloop.READ
        if self._write_buffer :
            state |= ioloop.WRITE
        if state != self._state:
            self._state = state
            self._iolooper.modify_handler(self._sock,self._state)

    def reading(self):
        return self._read_callback is not None

    def writing(self):
        return self._write_callback is not None

    def closed(self):
        return self._sock is None

    def _handle_read(self):
        try:
            chunk = self._sock.recv(self.read_chunk_size)
        except socket.error , args:
            if args[0] in (errno.EWOULDBLOCK,errno.EAGAIN):
                return
            self.close()
            raise
        if not chunk :
            self.close()
            return
        self._read_buffer += chunk
        if len(self._read_buffer) > self.max_buffer_size :
            print "read reached maximum buffer size"
            self.close()
            return
        if self.read_num_bytes:
            if len(self._read_buffer) >= self.read_num_bytes:
                callback               = self._read_callback
                loc                    = self.read_num_bytes
                self._read_callback    = None
                self.read_num_bytes    = None
                self._run_callback(callback,self._consume(loc))
                return
        elif self.read_delimiter:
            loc = self._read_buffer.find(self.read_delimiter)
            if loc != -1:
                callback = self._read_callback
                read_delimiter_len = len(self.read_delimiter)
                self._read_callback = None
                self._run_callback(callback, self._consume(loc + read_delimiter_len))
                return

    def _handle_write(self):
        try:
            num_bytes = self._sock.send(self._write_buffer)
            self._write_buffer = self._write_buffer[num_bytes:]
        except socket.error , args:
            if args[0] in (errno.EAGAIN,errno.EWOULDBLOCK):
                return
            self.close()
            raise
        if not self._write_buffer and self._write_callback:
            callback = self._write_callback
            self._write_callback = None
            self._run_callback(callback)
            return

    def read_until(self,delimiter,callback):
        assert not self._read_callback , "already reading"
        loc = self._read_buffer.find(delimiter)
        if loc != -1:
            self._run_callback(callback,self._consume(loc+len(delimiter)))
            return
        self._check_close()
        self._read_callback      = callback
        self.read_delimiter      = delimiter
        self._add_io_state(ioloop.READ)

    def read_bytes(self,num_bytes,callback):
        assert not self._read_callback, "already reading"
        self._check_close()
        if len(self._read_buffer) >= num_bytes:
            self._run_callback(callback,self._consume(num_bytes))
            return
        self._check_close()
        self._read_callback        = callback
        self.read_num_bytes        = num_bytes
        self._add_io_state(ioloop.READ)

    def write(self,chunk,callback=None):
        self._check_close()
        if len(chunk) + len(self._write_buffer) > self.max_buffer_size:
            print "reached maximum buffer size"
            return
        self._check_close()
        self._write_buffer   += chunk
        self._add_io_state(ioloop.WRITE)
        self._write_callback = callback

    def close(self):
        if self._sock == None:
            return
        self._iolooper.remove_handler(self._sock)
        self._sock.close()
        self._sock = None
        if self._close_callback:
            self._run_callback(self._close_callback)
            self._close_callback = None

    def _run_callback(self,callback,*args,**kwargs):
        try:
            callback(*args,**kwargs)
        except:
            pass

    def _consume(self,loc):
        res = self._read_buffer[:loc]
        self._read_buffer = self._read_buffer[loc:]
        return res

    # not a & b  == not (a & b)
    def _add_io_state(self,state):
        if not self._state & state : #如果事件已经注册监听就不需要再注册了
            self._state |= state
            self._iolooper.modify_handler(self._sock,self._state)

    def set_close_callback(self,callback):
        self._close_callback = callback

    def _check_close(self):
        if not self._sock:
            raise IOError("stream closed")


if __name__ == "__main__":
    print 1024*1024