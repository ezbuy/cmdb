# coding:utf-8
from django.conf.urls import patterns, include, url
from asset.views import *

urlpatterns = patterns('',
                       url(r'^list/$', asset_list, name='asset_list'),
                       url(r'^get/$', get, name='get'),
                       url(r'^goServices/$', goServices, name='goServices'),
                       url(r'^getData/$', getData, name='getData'),
                       url(r'^getServices/$', getServices, name='getServices'),
                       url(r'^goRevert/$', goRevert, name='goRevert'),
                       url(r'^goRevertResult/$', goRevertResult, name='goRevertResult'),
                       url(r'^revert/$', revert, name='revert'),
                       url(r'^goconf/$', goConfHTML, name='goConf'),
                       url(r'^goConfResult/$', goConfResult, name='goConfResult'),
                       url(r'^test/$', test, name='test'),
                       url(r'^getProjectList/$', getProjectList, name='getProjectList'),
                       url(r'^getConfProject/$', getConfProject, name='getConfProject'),
                       url(r'^getText/$', getText, name='getText'),
                       url(r'^gobuild/$', go_build, name='gobuild'),
                       url(r'^getBuildList/$', getBuildList, name='getBuildList'),
                       url(r'^build_go/$', build_go, name='build_go'),
                       url(r'^goStatus/$', go_status, name='go_status'),
                       url(r'^crontabUpdate/$', crontab_update, name='crontab_update'),
                       url(r'^cronjob_list/$', cronjob_list, name='cronjob_list'),
                       url(r'^go_template/$', go_template_html, name='go_template'),
                       url(r'^get_gotemplate_project/$', get_gotemplate_project, name='get_gotemplate_project'),
                       url(r'^go_template_result/$', go_template_result, name='go_template_result'),
                       url(r'^get_go_revert_list/$', get_go_revert_list, name='get_go_revert_list'),
                       url(r'^qcloud/$', qcloud, name='qcloud'),
                       url(r'^qingcloud/$', qingcloud, name='qingcloud'),
                       url(r'^group/list/$', asset_list, name='group_list'),  ### 资产组 ###
                       url(r'^idc/list/$', asset_list, name='idc_list'),  ### 机房 ###
                       )
