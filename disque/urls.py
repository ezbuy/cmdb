# -*- coding: utf-8 -*-

"""URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

from django.conf.urls import url

from disque import views

urlpatterns = [
    url(r'^ackjob/$', views.ackjob_index, name="ackjob"),
    url(r'^addjob/$', views.addjob_index, name="addjob"),
    url(r'^api/addjob/$', views.add_job),
    url(r'^api/ackjob/$', views.ack_job)
]
