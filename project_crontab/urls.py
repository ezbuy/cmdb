# coding:utf-8
from django.conf.urls import patterns, include, url
from project_crontab.views import *

urlpatterns = patterns('',
                       url(r'^cronList/$', crontabList, name='crontabList'),
                       url(r'^cronList/add/$', addCrontab, name='addCrontab'),
                       url(r'^cronList/modify/$', modifyCrontab, name='modifyCrontab'),
                       url(r'^cronList/del/$', delCrontab, name='delCrontab'),
                       url(r'^cronList/start/$', startCrontab, name='startCrontab'),
                       url(r'^cronList/pause/$', pauseCrontab, name='pauseCrontab'),
                       )
