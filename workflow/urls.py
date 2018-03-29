"""mico URL Configuration

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
from django.conf.urls import url,include
from django.contrib import admin
from workflow.views import index,get_hosts,my_tickets,get_ticket_tasks,submit_tickets,handle_tickets,handled_tasks
from workflow.views import get_svc_minions


urlpatterns = [
    url(r'^index/$', index, name='workflow_index'),
    url(r'^get_hosts/$', get_hosts, name='get_hosts'),
    url(r'^my_tickets/$', my_tickets, name='my_tickets'),
    url(r'^get_ticket_tasks/$', get_ticket_tasks, name='get_ticket_tasks'),
    url(r'^submit_tickets/$', submit_tickets, name='submit_tickets'),
    url(r'^handle_tickets/$', handle_tickets, name='handle_tickets'),
    url(r'^handled_tasks/$', handled_tasks, name='handled_tasks'),
    url(r'^svc_minions/$', get_svc_minions, name='get_svc_minions'),
]