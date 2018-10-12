# -*- coding:utf-8

"""
header
length
method
\r\n\r\n
body
"""

class SUPPORT_METHOD(object):
    ON_OPEN          = "on_open"
    ON_CLOSE         = "on_close"
    ON_MESSAGE       = "on_message"
    ON_PING          = "on_ping"
    ON_PANG          = "on_pong"

def parse_header(header):
    header   = header[:len(header) - 4]
    headers  = header.split(",")
    header   = dict()
    for h in headers :
        k_v = h.split(":")
        header[k_v[0]] = k_v[1]
    return header

def wrap_msg(method,body):
    length = len(body)
    msg = "method:"+method+","+"length:"+str(length)+"\r\n\r\n"+body
    return msg

def ping():
    return wrap_msg(SUPPORT_METHOD.ON_PING,"")

def pong():
    return wrap_msg(SUPPORT_METHOD.ON_PANG,"")

if __name__ == "__main__":
    print wrap_msg(SUPPORT_METHOD.ON_CLOSE,"i love you")