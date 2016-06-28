# coding:utf-8
from django.conf.urls import patterns, include, url
from asset.views import *

urlpatterns = patterns('',
    url(r'^list/$', asset_list, name='asset_list'),
    url(r'^get/$', get, name='get'),
    url(r'^goServices/$', goServices, name='goServices'),
    url(r'^getData/$', getData, name='getData'),
    url(r'^getServices/$', getServices, name='getServices'),
    url(r'^goRevert/$', goRevert, name='goRevert'),
    url(r'^goRevertResult/$', goRevertResult, name='goRevertResult'),
    url(r'^goRevertResulttwo/$',goRevertResulttwo,name='goRevertResulttwo'),
    url(r'^revert/$',revert, name='revert'),
    url(r'^goconf/$',goConfHTML,name='goConf'),
    url(r'^goConfResult/$', goConfResult, name='goConfResult'),
    url(r'^test/$', test, name='test'),
    url(r'^getProjectList/$', getProjectList, name='getProjectList'),
)