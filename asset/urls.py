# coding:utf-8
from django.conf.urls import patterns, include, url
from asset.views import *

urlpatterns = patterns('',
    url(r'^list/$', asset_list, name='asset_list'),
    url(r'^get/$', get, name='get'),
    url(r'^goServices/$', goServices, name='goServices'),
    url(r'^getData/$', getData, name='getData'),
)