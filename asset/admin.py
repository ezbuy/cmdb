from django.contrib import admin
from asset.models import *
# Register your models here.


class goServicesAdmin(admin.ModelAdmin):
    list_display = ('ip','name','env','group','saltminion')

class svnAdmin(admin.ModelAdmin):
    list_display = ('username','password','repo','localpath','movepath','revertpath')
admin.site.register(IDC)
admin.site.register(Asset)
admin.site.register(AssetRecord)
admin.site.register(AssetGroup)
admin.site.register(minion)
admin.site.register(goservices,goServicesAdmin)
admin.site.register(gogroup)
admin.site.register(svn,svnAdmin)