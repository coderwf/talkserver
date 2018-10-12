# -*- coding:utf-8 -*-
#handler传入application作为map
#application传入server作为执行器
#application 实现__call__方法
#application解析自己的handler,application获得request,解析参数传给exe并
#执行handler._execute(*args,**kwargs)方法
#而且每次都实例化了一个信息handler类,就可以有办法将参数传到handler中使用

#handler中_execute() 使用getaddr(self,method)执行自己的被覆盖的方法

#或者直接使用handler,实现_call__(),在里面使用self.__getattributename__(method)()一样可以
#自己解析handler

#初级阶段直接使用第二个方法

#-------------------------------------------------------------------------------
"""handler中会包含一个connection
application负责传递handler实例
"""
from evpoll import _epoll
import ioloop
from servers import TcpServer
import time
import pf

#每次write
#用户接口

#application负责管理handler
class Application(object):
    def __init__(self,handler_class):
        self.conns          = {}  #conn : handler
        self.handler_class  = handler_class

    #关闭某个连接
    def close_connection(self,connection):
        connection.close()
        self.conns.pop(connection,None)
    #
    def __call__(self, tcp_req):
        method       = tcp_req.get_method()
        connection   = tcp_req.get_connection()
        message      = tcp_req.get_message()
        handler      = self.conns.get(connection,None)
        if handler == None:
            handler = self.handler_class(self,connection)
            self.conns[connection] = handler
            handler.set_request(tcp_req)
        handler.update_active_time()  #更新最近给服务器发送消息时间
        if method in pf.SUPPORT_METHOD.ON_PING :
            handler.flush(pf.pong())
            return
        if method in pf.SUPPORT_METHOD.ON_CLOSE :
            self.close_connection(connection)
        handler._execute(method,message)
        return


class TcpHandler(object):
    def __init__(self,application,connection):
        self.closed          = False
        self.request         = None
        self._timeout        = 4000   #ms
        self._active_time    = time.time()   #最后一次活跃时间
        self._write_buffer   = ""
        self._connection     = connection
        self._application    = application

    def set_request(self,request):
        self.request = request

    def update_active_time(self):
        self._active_time = time.time()

    #延时多久没收到消息则关闭连接
    def set_timeout(self,timeout):
        self._timeout  = timeout

    def on_open(self,*args,**kwargs):
        raise TcpError(405,"on open not impl")

    def on_close(self,*args,**kwargs):
        print "on close"
        raise TcpError(405, "on close not impl")

    def on_message(self,*args,**kwargs):
        raise TcpError(405, "on close not impl")

    def close(self):
        self.closed = True
        msg = pf.wrap_msg(pf.SUPPORT_METHOD.ON_CLOSE,"")
        self._connection.write(msg)
        self._application.close_connection(self._connection)

    def ping(self):
        pass

    def write(self,chunk):
        if self.closed :
            raise IOError("connection closed")
        now = time.time()
        if now - self._active_time > self._timeout:
            self.close()
            raise IOError("connection closed")
        self._write_buffer += chunk

    def flush(self,chunk = ""):
        if self.closed :
            raise IOError("connection closed")
        self._write_buffer += chunk
        now = time.time()
        if now - self._active_time > self._timeout:
            self.close()
            raise IOError("connection closed")
        self._connection.write(self._write_buffer)
        self._write_buffer = ""

    def _execute(self,method,*args,**kwargs):
        print "method>>>>>>>>>",method
        print "get attr",getattr(self,method)
        getattr(self,method)(*args,**kwargs)



class TcpError(Exception):
    def __init__(self,code,msg):
        self.code = code
        self.msg  = msg

    def __str__(self):
        print "error_code",self.code
        print "info",self.msg


class MyHandler(TcpHandler):
    conns = set()
    # def on_close(self,*args,**kwargs):
    #     pass

    def on_open(self,*args,**kwargs):
        self.conns.add(self)
        print "client come ..."

    def on_message(self,message):
        print message


if __name__ == "__main__":
    impl = _epoll()
    iolooper = ioloop.IoLoop(impl)
    app = Application(MyHandler)
    server = TcpServer(iolooper, app)
    server.listen(9999, "127.0.0.1")
    server.start()