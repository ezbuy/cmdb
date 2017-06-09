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
from users.views import user_list,user_add_html,user_add,user_edit,user_is_active

urlpatterns = [
    url(r'^user_list/$', user_list, name='user_list'),
    url(r'^user_add_html/$', user_add_html, name='user_add_html'),
    url(r'^user_add/$', user_add, name='user_add'),
    url(r'user_edit/(?P<id>\d+)/$', user_edit, name='user_edit'),
    url(r'^user_is_active/(?P<id>\d+)/$', user_is_active, name='user_is_active'),
]