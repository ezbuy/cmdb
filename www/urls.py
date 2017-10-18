# coding:utf-8
from django.conf.urls import patterns, include, url
from www.views import *

urlpatterns = patterns('',
    url(r'^list/$', list, name='www_list'),
    url(r'^wwwList$',wwwList,name='wwwList'),
    url(r'^getProjectName$',getProjectName,name='getProjectName'),
    url(r'^deployIis$',deployIis,name='deployIis'),
    url(r'^recycleList$', recycleList, name='recycleList'),
    url(r'^deployRecycle$', deployRecycle, name='deployRecycle'),
    url(r'^wwwRevertList$', wwwRevertList, name='wwwRevertList'),
    url(r'^deployRevertIis$', deployRevertIis, name='deployRevertIis'),
    url(r'^getGroup$', getGroup, name='getGroup'),
    url(r'^deployGroup$', deployGroup, name='deployGroup'),
)