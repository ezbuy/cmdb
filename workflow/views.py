from django.shortcuts import render,HttpResponse
from django.contrib.auth.decorators import login_required
from asset.utils import deny_resubmit
from models import TicketType,TicketTasks
import json
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
    pass
