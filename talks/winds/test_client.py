# -*- coding:utf-8 -*-
import pf
import socket
import errno
#----------------------------------------
import threading
class AccThread(threading.Thread):
    def __init__(self,sock):
        threading.Thread.__init__(self)
        self.sock  = sock

    def run(self):
        while True :
            try:
                acc = self.sock.recv(1024)
                print acc
            except socket.error , args:
                if args[0] in (errno.EWOULDBLOCK,errno.EAGAIN):
                    continue
                return

class Client(object):
    def __init__(self):
        self.sock = None

    def connect(self,port,address):
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.sock.setblocking(True)
        try:
            self.sock.connect((address, port))
            msg = pf.wrap_msg(pf.SUPPORT_METHOD.ON_OPEN,"")
            self.sock.send(msg)
        except Exception , e:
            print e
        AccThread(self.sock).start()

    def _check_closed(self):
        if not self.sock :
            raise IOError("stream is closed")

    def send_msg(self,msg):
        self._check_closed()
        msg = pf.wrap_msg(pf.SUPPORT_METHOD.ON_MESSAGE, msg)
        self.sock.send(msg)

    def close(self):
        self._check_closed()
        self.send_close()
        self.sock.close()
        self.sock = None

    def send_close(self):
        msg = pf.wrap_msg(pf.SUPPORT_METHOD.ON_CLOSE, "")
        self.sock.send(msg)


if __name__ == "__main__":
    client = Client()
    client.connect(9999,"127.0.0.1")
    while True:
        msg = raw_input()
        if msg == "close":
            client.close()
        else:
            client.send_msg(msg)

