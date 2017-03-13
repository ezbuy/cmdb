from django.shortcuts import render,render_to_response,HttpResponse
from django.contrib.auth.decorators import login_required
from subversion.models import subversion
import json,requests
from salt.client import LocalClient
from asset.utils import logs,deny_resubmit,dingding_robo

saltCmd = LocalClient()


@login_required
@deny_resubmit(page_key='deploy_svn_add_repo')
def subversionCreate(request):
    return render(request,'subversioncreate.html')

@login_required
@deny_resubmit(page_key='deploy_svn_add_user')
def subversionAddUserHtml(request):
    return render(request,'subversionadduser.html')

@login_required
def getSubversionHost(request):

    env = request.GET['env']
    obj = subversion.objects.filter(env=env)
    result = []
    for h in obj:
        result.append(str(h.hostname.saltname))
    return HttpResponse(json.dumps(result))


@login_required
@deny_resubmit(page_key='deploy_svn_add_repo')
def createRepo(request):
    result = []
    username = request.user
    ip = request.META['REMOTE_ADDR']

    env = request.POST['env']
    host = request.POST['hostname']
    svnName =  request.POST['svnName']
    obj = subversion.objects.filter(env=env)
    for info in obj:
        if info.hostname.saltname == host:
            svnparentpath = info.svnparentpath
            svnowner = info.svnowner
            svnrooturl = info.svnrooturl
            svnusername = info.svnusername
            svnpassword = info.svnpassword

    try:
        cmdinfo = saltCmd.cmd(host,'cmd.run',['svnadmin create %s%s && chown -R %s %s%s' % (svnparentpath,svnName,svnowner,svnparentpath,svnName)])
        if cmdinfo[host] == '':
            cmdinfo[host] = 'Successful'
            result.append(cmdinfo)
            r = requests.session()
            r.auth = (svnusername,svnpassword)
            test_url = r.get(svnrooturl + svnName)
            if test_url.status_code == 200:
                repo_info = "The svn repo url is %s%s." %(svnrooturl,svnName)
                mes = {host:repo_info}
                result.append(mes)
                notification_mes = 'It is successful.'
            else:
                notification_mes = 'It is error.'
        else:
            result.append(cmdinfo)
            notification_mes = 'It is error.'
    except Exception,e:
            print e
            result.append(cmdinfo)
            notification_mes = 'The system is error.....'

    dingding_robo(host,'create svn repo "%s"' % svnName,notification_mes,username,request.POST['phone_number'])
    logs(username,ip,'create svn repo "%s"' %svnName,notification_mes)


    return render(request, 'getdata.html', {'result': result})


@login_required
@deny_resubmit(page_key='deploy_svn_add_user')
def svnAddUser(request):
    username = request.user
    ip = request.META['REMOTE_ADDR']
    env = request.POST['env']
    host = request.POST['hostname']
    svnName = request.POST['svnName']
    svnPassword = request.POST['svnPassword']
    result = []

    obj = subversion.objects.filter(env=env)
    try:
        for info in obj:
            if info.hostname.saltname == host:
                svnPasswordFile = info.svnpasswordfile
                cmdinfo = saltCmd.cmd(host,'cmd.run',['htpasswd -b %s %s %s'%(svnPasswordFile,svnName,svnPassword)])
    except Exception,e:
        print e
        cmdinfo = {host:"Internal Server Error"}

    result.append(cmdinfo)
    dingding_robo(host,"svn adduser %s " % svnName,cmdinfo,username,request.POST['phone_number'])
    logs(username,ip,"svn adduser %s " % svnName,cmdinfo)
    return render(request, 'getdata.html', {'result': result})

