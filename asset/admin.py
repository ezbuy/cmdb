from django.contrib import admin
from asset.models import *
# Register your models here.


class goServicesAdmin(admin.ModelAdmin):
    list_display = ('ip','name','env','group','saltminion','owner','has_statsd','has_sentry','comment','ports','level')
    search_fields = ['name','owner']

class svnAdmin(admin.ModelAdmin):
    list_display = ('username','password','repo','localpath','movepath','revertpath','executefile','project')

class goconfAdmin(admin.ModelAdmin):
    list_display = ('username','password','repo','localpath','env','project','hostname')

class assetAdmin(admin.ModelAdmin):
    list_display = ('hostname','ip','system_type','asset_type','cpu','memory','wan_ip')
    search_fields = ['hostname','ip','asset_type','wan_ip']

class gobuildAdmin(admin.ModelAdmin):
    list_display = ('env','hostname')

class gostatusAdmin(admin.ModelAdmin):
    list_display = ('hostname','supervisor_host','supervisor_username','supervisor_password','supervisor_port')

class crontabSVNAdmin(admin.ModelAdmin):
    list_display = ('hostname','username','password','repo','localpath','project')

class minionAdmin(admin.ModelAdmin):
    list_display = ('saltname','ip')
    search_fields = ['saltname']

class gotemplateAdmin(admin.ModelAdmin):
    list_display = ('username','password','repo','localpath','env','project','hostname')
    search_fields = ['repo']

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user','phone_number')

class GoServiceRevisionAdmin(admin.ModelAdmin):
    list_display = ('name','last_rev','last_clock', 'gotemplate_last_rev')
    search_fields = ['name']

class CronMinionAdmin(admin.ModelAdmin):
    list_display = ('name','saltminion')
    search_fields = ['name']

admin.site.register(IDC)
admin.site.register(Asset,assetAdmin)
admin.site.register(AssetRecord)
admin.site.register(AssetGroup)
admin.site.register(minion,minionAdmin)
admin.site.register(goservices,goServicesAdmin)
admin.site.register(gogroup)
admin.site.register(svn,svnAdmin)
admin.site.register(goconf,goconfAdmin)
admin.site.register(gobuild,gobuildAdmin)
admin.site.register(gostatus,gostatusAdmin)
admin.site.register(crontab_svn,crontabSVNAdmin)
admin.site.register(GOTemplate,gotemplateAdmin)
admin.site.register(UserProfile,UserProfileAdmin)
admin.site.register(GoServiceRevision,GoServiceRevisionAdmin)
admin.site.register(cron_minion,CronMinionAdmin)
