# coding:utf-8
from django.conf.urls import patterns, include, url
from kettle.views import kettle_index,kettle_execute


urlpatterns = [
    url(r'^kettle_index/$', kettle_index, name='kettle_index'),
    url(r'^kettle_execute/$', kettle_execute, name='kettle_execute'),
]