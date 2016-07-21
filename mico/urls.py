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
from cmdb.views import index
from web.views import login,logout


import asset,logs,winservices,cache,www

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$',index,name='index'),
    url(r'^asset/', include('asset.urls')),
    url(r'^logs/', include('logs.urls')),
    url(r'^winservices/', include('winservices.urls')),
    url(r'^cache/', include('cache.urls')),
    url(r'^www/', include('www.urls')),
    url(r'^login/',login,name='login'),
    url(r'^logout/',logout,name='logout'),

]