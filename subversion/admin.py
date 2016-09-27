from django.contrib import admin

# Register your models here.

from subversion.models import subversion


class subversionAdmin(admin.ModelAdmin):
    list_display = ('env','hostname','svnparentpath','svnowner','svnrooturl','svnusername','svnpassword','svnpasswordfile')

admin.site.register(subversion,subversionAdmin)
