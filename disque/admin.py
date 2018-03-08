# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from disque.models import ClusterInfo

# Register your models here.


class ClusterInfoAdmin(admin.ModelAdmin):
    list_display = ('name', 'addr')
    search_fields = ['name']


admin.site.register(ClusterInfo, ClusterInfoAdmin)
