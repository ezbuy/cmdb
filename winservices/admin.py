from django.contrib import admin
from winservices.models import winconf
# Register your models here.

class winconfAdmin(admin.ModelAdmin):
    list_display = ('username','password','repo','localpath','env','servicename','hostname','tasklist_name')


admin.site.register(winconf,winconfAdmin)