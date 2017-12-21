# -*- coding: utf-8 -*-
from django.conf.urls import url
from command_job.views import command_index, command_req

urlpatterns = [
    url(r'^command_index/$', command_index, name='command_index'),
    url(r'^command_req/$', command_req, name='command_req'),
]
