# coding:utf-8
from django.conf.urls import patterns, include, url
from www.views import *

urlpatterns = patterns('',
    url(r'^list/$', list, name='www_list'),

)