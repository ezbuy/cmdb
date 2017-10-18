from django.contrib import admin

# Register your models here.
from www.models import *


class webSiteAdmin(admin.ModelAdmin):
    list_display = ('webSite','salt_pillar_host','svn_path','recycle_cmd','env')


admin.site.register(webSite,webSiteAdmin)
admin.site.register(salt_module)
admin.site.register(webUrl)
admin.site.register(groupName)