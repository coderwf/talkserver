# -*- coding:utf-8 -*-

import os

class Handler(object):
    def get(self,*args,**kwargs):
        print "exe"

    def _execute(self,*args,**kwargs):
        getattr(self,"get")(*args,**kwargs)


    def __call__(self, request):
        self.__getattribute__("get")(request)

def fun1():
    ha = Handler()
    ha(4)

if __name__ == "__main__":
    fun1()