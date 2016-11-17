from django.contrib import admin
from asset.models import *
# Register your models here.


class goServicesAdmin(admin.ModelAdmin):
    list_display = ('ip','name','env','group','saltminion')

class svnAdmin(admin.ModelAdmin):
    list_display = ('username','password','repo','localpath','movepath','revertpath','executefile','project')

class goconfAdmin(admin.ModelAdmin):
    list_display = ('username','password','repo','localpath','env','project','hostname')

class assetAdmin(admin.ModelAdmin):
    list_display = ('hostname','ip','system_type','asset_type','cpu','memory')

class gobuildAdmin(admin.ModelAdmin):
    list_display = ('env','hostname')

class gostatusAdmin(admin.ModelAdmin):
    list_display = ('hostname','supervisor_host','supervisor_username','supervisor_password','supervisor_port')


admin.site.register(IDC)
admin.site.register(Asset,assetAdmin)
admin.site.register(AssetRecord)
admin.site.register(AssetGroup)
admin.site.register(minion)
admin.site.register(goservices,goServicesAdmin)
admin.site.register(gogroup)
admin.site.register(svn,svnAdmin)
admin.site.register(goconf,goconfAdmin)
admin.site.register(gobuild,gobuildAdmin)
admin.site.register(gostatus,gostatusAdmin)