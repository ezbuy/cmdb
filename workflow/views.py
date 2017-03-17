from django.shortcuts import render,HttpResponse
from django.contrib.auth.decorators import login_required
from asset.utils import deny_resubmit
from models import TicketType
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
    hosts = []
    for host in obj.hosts.values():
        hosts.append(host['saltname'])
    return HttpResponse(json.dumps(hosts))
