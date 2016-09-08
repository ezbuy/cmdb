from django.shortcuts import render,render_to_response,HttpResponse
from django.contrib.auth.decorators import login_required
from subversion.models import subversion
import json,requests
from salt.client import LocalClient
from asset.utils import notification,logs



@login_required
def subversionCreate(request):
    return render(request,'subversioncreate.html')

@login_required
def getSubversionHost(request):

    env = request.GET['env']
    obj = subversion.objects.filter(env=env)
    result = []
    for h in obj:
        result.append(str(h.hostname.saltname))
    return HttpResponse(json.dumps(result))


@login_required
def createRepo(request):
    result = []
    saltCmd = LocalClient()
    username = request.user
    ip = request.META['REMOTE_ADDR']

    env = request.GET['env']
    host = request.GET['hostname']
    svnName =  request.GET['svnName']
    obj = subversion.objects.filter(env=env)
    for info in obj:
        if info.hostname.saltname == host:
            svnparentpath = info.svnparentpath
            svnowner = info.svnowner
            svnrooturl = info.svnrooturl
            svnusername = info.svnusername
            svnpassword = info.svnpassword


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

    notification(host,'create svn repo "%s"' % svnName,notification_mes,username)
    logs(username,ip,'create svn repo "%s"' %svnName,notification_mes)


    return render(request, 'getdata.html', {'result': result})