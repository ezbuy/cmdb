from django.contrib import admin
from asset.models import *
# Register your models here.


class goServicesAdmin(admin.ModelAdmin):
    list_display = ('ip','name','env','group','saltminion')
admin.site.register(IDC)
admin.site.register(Asset)
admin.site.register(AssetRecord)
admin.site.register(AssetGroup)
admin.site.register(minion)
admin.site.register(goservices,goServicesAdmin)
admin.site.register(gogroup)