from django.shortcuts import render, render_to_response, HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required

from asset.utils import *
from project_crontab.models import *


@login_required
@deny_resubmit(page_key='cronSvn')
def cronSvn(request):
    svn_list = Svn.objects.all().order_by('salt_minion__saltname').values('id', 'salt_minion__saltname', 'salt_minion__ip', 'repo', 'local_path', 'creator__username', 'create_time')
    print svn_list
    svnlist_with_chinesename = []
    print svnlist_with_chinesename
    return render(request, 'project_crontab/svn_list.html', {'svn_list': svn_list})


@login_required
def cronProjectList(request):
    project_list = Project.objects.all().order_by('name')
    return render(request, 'project_crontab/project_list.html', {'project_list': project_list})


@login_required
def crontabList(request):
    crontab_list = CrontabCmd.objects.all().order_by('project__name', 'cmd')
    return render(request, 'project_crontab/crontab_list.html', {'crontab_list': crontab_list})
