from django.contrib import admin

from config_center.models import Resources, SVCResources, ResTypes


# Register your models here.


class ResourcesAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'category', 'comment')


class SVCResourcesAdmin(admin.ModelAdmin):
    list_display = ('svc', 'res')


class ResTypesAdmin(admin.ModelAdmin):
    list_display = ('name',)


admin.site.register(Resources, ResourcesAdmin)
admin.site.register(SVCResources, SVCResourcesAdmin)
admin.site.register(ResTypes, ResTypesAdmin)
