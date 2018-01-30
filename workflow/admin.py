# coding: utf-8
from django.contrib import admin
from workflow.models import TicketType,TicketTasks,TicketOperating,WebInfo

# Register your models here.


class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ('type_name','create_time','modify_time','state')

class TicketTasksAdmin(admin.ModelAdmin):
    list_display = ('tasks_id','title','ticket_type','creator','handler','content','create_time','modify_time','state')

class TicketOperatingAdmin(admin.ModelAdmin):
    list_display = ('operating_id','submitter','handler','create_time','modify_time','content','result')

class WebInfoAdmin(admin.ModelAdmin):
    list_display = ('site_name','site_value','type')

admin.site.register(TicketType,TicketTypeAdmin)
admin.site.register(TicketTasks,TicketTasksAdmin)
admin.site.register(TicketOperating,TicketOperatingAdmin)
admin.site.register(WebInfo,WebInfoAdmin)


