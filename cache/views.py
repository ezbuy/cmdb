from django.shortcuts import render,render_to_response,HttpResponse
from django.contrib.auth.decorators import login_required
from asset.utils import logs,notification
from salt.client import LocalClient
from cache.models import memcache
# Create your views here.


@login_required
def memcached(request):
    if 'env' in request.GET:
        env = request.GET['env']
    else:
        env = 1
    mc = memcache.objects.filter(env=env)


    return render_to_response("memcachelist.html",{'project':mc})


@login_required
def flushMemcached(request):
    data = request.GET.getlist('mcName')
    saltCmd = LocalClient()
    result = []


    for name in data:
        for info in memcache.objects.filter(memcacheName=name):
            try:
                cmd = saltCmd.cmd(info.saltMinion.saltname,'cmd.run',['echo "flush_all" | nc %s %s' % (info.ip,info.port)])
                result.append(cmd)
                print result
            except Exception,e:
                print e

    return render_to_response('getdata.html',{'result':result})
