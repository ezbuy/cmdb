# coding:utf-8
from django.conf.urls import patterns, include, url
from project_crontab.views import *

urlpatterns = patterns('',
                       url(r'^cronSvn/$', cronSvn, name='cronSvn'),
                       url(r'^cronProjectList/$', cronProjectList, name='cronProjectList'),
                       url(r'^crontabList/$', crontabList, name='crontabList'),
                       )
