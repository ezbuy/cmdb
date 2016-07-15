from django.contrib import admin
from cache.models import *
# Register your models here.


class cacheAdmin(admin.ModelAdmin):
    list_display = ('memcacheName','env','saltMinion','ip','port')



admin.site.register(memcache,cacheAdmin)