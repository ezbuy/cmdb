from django.shortcuts import render,render_to_response,HttpResponse
from django.contrib.auth.decorators import login_required
from asset.utils import logs,dingding_robo,deny_resubmit
from salt.client import LocalClient
from cache.models import memcache
# Create your views here.


@login_required
@deny_resubmit(page_key='memcache')
def memcached(request):
    if 'env' in request.GET:
        env = request.GET['env']
    else:
        env = 1
    mc = memcache.objects.filter(env=env)


    return render(request,"memcachelist.html",{'project':mc})


@login_required
@deny_resubmit(page_key='memcache')
def flushMemcached(request):
    data = request.POST.getlist('mcName')
    project = 'memcache flush'
    username = request.user
    ip = request.META['REMOTE_ADDR']
    saltCmd = LocalClient()
    result = []

    for name in data:
        for info in memcache.objects.filter(memcacheName=name):
            try:
                cmd = saltCmd.cmd(info.saltMinion.saltname,'cmd.run',['echo "flush_all" | nc %s %s' % (info.ip,info.port)])
                result.append(cmd)
                if cmd[info.saltMinion.saltname] == 'OK':
                    msg = 'Success'
                else:
                    msg = 'error'
                host = info.ip + ":" + info.port
                dingding_robo(host,project,msg,username,request.POST['phone_number'])
                print result
            except Exception,e:
                print e
    logs(username,ip,project,result)

    return render(request,'getdata.html',{'result':result})
