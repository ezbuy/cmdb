# -*- coding: utf-8 -*-
from django.conf.urls import url
from consul_kv.views import consul_kv_index, consul_kv_req

urlpatterns = [
    url(r'^index/$', consul_kv_index, name='consul_kv_index'),
    url(r'^req/$', consul_kv_req, name='consul_kv_req'),
]
