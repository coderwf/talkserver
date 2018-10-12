# -*- coding:utf-8 -*-

import socket
import ioloop
import errno
from iostream import IoStream
import pf
from functools import partial
from evpoll import _epoll
#------------------------------------------------------------------------------


class TcpServer(object):
    def __init__(self,iolooper,request_callback):
        self._sock               = None
        self._iolopper           = iolooper
        self.request_callback    = request_callback

    #设置execlose
    def listen(self,port,address=""):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.bind((address,port))
        self._sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self._sock.setblocking(False)
        self._sock.listen(128)
        self._iolopper.add_handler(self._sock,self._handle_acception,ioloop.READ)

    #将其注册到iolooper中监听
    def _handle_acception(self,fd,events):
        for i in range(0,128):
            try:
                conn , address = self._sock.accept()
                stream = IoStream(conn,self._iolopper)
                TcpConnection(stream, address,self.request_callback)
            except socket.error , args:
                if args[0] in (errno.EWOULDBLOCK,errno.EAGAIN):
                    continue
                raise

    def _check_closed(self):
        if not self._sock :
            raise IOError("sock closed")

    def start(self):
        self._check_closed()
        self._iolopper.start()

    def stop(self):
        if self._sock:
            self._sock.close()
            self._iolopper.remove_handler(self._sock)
            self._sock  = None


class TcpConnection(object):
    def __init__(self,stream,address,request_callback):
        self.stream               = stream
        self.address              = address
        self._closed              = False
        self.request_callback     = request_callback
        self.stream.read_until("\r\n\r\n",self._on_header)

    def _on_header(self,header):
        header  = pf.parse_header(header)
        length  = header.get("length")
        length  = int(length)
        method  = header.get("method")
        tcp_req = TcpReq(self,method)
        self.stream.read_bytes(length,partial(self._finish_request,tcp_req))

    def _finish_request(self,tcp_req,message):
        tcp_req.message = message
        self.request_callback(tcp_req)
        if self._closed :
            return
        self.stream.read_until("\r\n\r\n",self._on_header)

    def close(self):
        if not self._closed:
            self._closed = True
            self.stream.close()

    def write(self,chunk):
        self._check_close()
        self.stream.write(chunk)

    def _check_close(self):
        if self._closed :
            raise IOError("connection closed")


#某一个从客户端收到的消息的封装
#将connection封装在req中传给applicatin
class TcpReq(object):
    def __init__(self,conn,method):
        self.conn         = conn
        self.method       = method
        self.message      = None

    def get_message(self):
        return self.message

    def get_connection(self):
        return self.conn

    def get_method(self):
        return self.method


#自定义消息的类型方法实现
def rquest_callback(tcp_req):
    print tcp_req.msg
    tcp_req.write("i love you too")
    tcp_req.flush()


if __name__ == "__main__":
    impl = _epoll()
    iolooper = ioloop.IoLoop(impl)
    server = TcpServer(iolooper,rquest_callback)
    server.listen(9999,"127.0.0.1")
    server.start()

