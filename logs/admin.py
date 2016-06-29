from django.contrib import admin
from logs.models import *
# Register your models here.
class goLogAdmin(admin.ModelAdmin):
    list_display = ('user','remote_ip','goAction','result','datetime')

admin.site.register(goLog,goLogAdmin)