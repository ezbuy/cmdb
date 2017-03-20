from django.shortcuts import render,HttpResponse
from django.contrib.auth.decorators import login_required
from asset.utils import deny_resubmit
from models import TicketType,TicketTasks,TicketOperating
import json
import uuid
from django.contrib.auth.models import User

# Create your views here.
@login_required
@deny_resubmit(page_key='workflow_index')
def index(request):
    ticket_type = TicketType.objects.all()
    return render(request,'workflow_index.html',{'ticket_type':ticket_type})


@login_required
def get_hosts(request):
    ticket_type = request.GET['ticket_type']
    print '---------,',ticket_type
    obj = TicketType.objects.get(type_name=ticket_type)
    content = []
    hosts = []
    handler = []
    for host in obj.hosts.values():
        hosts.append(host['saltname'])
    content.append(hosts)
    for info in obj.handler.values():
        handler.append(info['username'])
    content.append(handler)
    print "----content----",content
    return HttpResponse(json.dumps(content))

@login_required
def my_tickets(request):
    tasks = TicketTasks.objects.filter(creator=request.user)
    return render(request,'my_tickets.html',{'tasks':tasks})



@login_required
def get_ticket_tasks(request):
    username = User.objects.get(username=request.user)
    tasks = TicketTasks.objects.filter(handler=username).filter(state='1')
    return render(request,'get_ticket_tasks.html',{'tasks':tasks})

@login_required
def submit_tickets(request):
    title = request.GET['title']
    ticket_type = request.GET['ticket_type']
    hosts = request.GET.getlist('hosts')
    project = request.GET['project']
    go_command = request.GET['go_command']
    supervisor_name =  request.GET['supervisor_name']
    svn_repo = request.GET['svn_repo']
    statsd = request.GET['statsd']
    sentry = request.GET['sentry']
    handler = request.GET['handler']

    salt_command = '''salt '%s' state.sls goservices.supervisor_submodule pillar=\'{
        "goprograme":"%s",
        "svnrepo":"%s",
        "supProgrameName":"%s",
        "goRunCommand":"%s -c /srv/goconf/%s/conf/conf.cmtpl"}\'''' % (','.join(hosts),project,svn_repo,supervisor_name,go_command,project)
    
    ticket_type = TicketType.objects.get(type_name=ticket_type)
    handler = User.objects.get(username=handler)
    task_id = str(uuid.uuid1())
    TicketTasks.objects.create(tasks_id=task_id,title=title,ticket_type=ticket_type,creator=request.user,content=salt_command,handler=handler,state='1')
    print '--------',request.GET
    print hosts
    print salt_command
    return render(request,'get_ticket_tasks.html')


@login_required
def handle_tickets(request):
    task_id = request.GET['id']
    submit = request.GET['submit']
    reply = request.GET['reply']
    operating_id = TicketTasks.objects.get(tasks_id=task_id)
    username = User.objects.get(username=request.user)
    if submit == 'reject':
        TicketTasks.objects.filter(tasks_id=task_id).update(state='4')
        TicketOperating.objects.create(operating_id=operating_id,handler=username,content=reply,result='2')
    salt_command = TicketTasks.objects.get(tasks_id=task_id).content
    print salt_command
    return render(request,'get_ticket_tasks.html')

