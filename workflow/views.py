from django.shortcuts import render,HttpResponse
from django.contrib.auth.decorators import login_required
from asset.utils import deny_resubmit,logs
from models import TicketType,TicketTasks,TicketOperating
from django.contrib.auth.models import User
from django.db.models import Q
from salt_api.api import SaltApi
from asset.models import gogroup,svn,minion,GOTemplate,goservices,gostatus,UserProfile
from mico.settings import svn_username,svn_password,go_local_path,go_move_path,go_revert_path,svn_gotemplate_repo,svn_gotemplate_local_path,webpage_host
from asset.utils import dingding_robo
import json
import uuid
import xmlrpclib
salt_api = SaltApi()


# Create your views here.
@login_required
@deny_resubmit(page_key='submit_tickets')
def index(request):
    ticket_type = TicketType.objects.all()
    return render(request,'workflow_index.html',{'ticket_type':ticket_type})


@login_required
def get_hosts(request):
    ticket_type = request.GET['ticket_type']
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
    return HttpResponse(json.dumps(content))

@login_required
def my_tickets(request):
    tasks = TicketTasks.objects.filter(creator=request.user).order_by('-modify_time')
    return render(request,'my_tickets.html',{'tasks':tasks})



@login_required
@deny_resubmit(page_key='handle_tickets')
def get_ticket_tasks(request):
    username = User.objects.get(username=request.user)
    tasks = TicketTasks.objects.filter(handler=username).filter(Q(state='1') | Q(state='5')).order_by('-modify_time')
    return render(request,'get_ticket_tasks.html',{'tasks':tasks})
    
@login_required
@deny_resubmit(page_key='submit_tickets')
def submit_tickets(request):
    title = request.POST['title']
    ticket_type = request.POST['ticket_type']
    handler = request.POST['handler']
    owner = str(request.user)
    if ticket_type == 'go':
        function = request.POST['function']
        hosts = request.POST.getlist('hosts')
        project = request.POST['project']
        go_command = request.POST['go_command']
        supervisor_name =  request.POST['supervisor_name']
        svn_repo = request.POST['svn_repo']
        statsd = request.POST['statsd']
        sentry = request.POST['sentry']
        go_command = go_command + " -c /srv/gotemplate/%s/conf.ctmpl" % project
        
        salt_command = {
            "title":title,
            "ticket_type":ticket_type,
            "function":function,
            "hosts":hosts,
            "project":project,
            "svn_repo":svn_repo,
            "supervisor_name":supervisor_name,
            "go_command":go_command,
            "statsd":statsd,
            "sentry":sentry,
            "handler":handler,
            "owner":owner
        }

    elif ticket_type == 'webpage':
        print '--------site_name-----:',request.POST.getlist('site_name')
        site_name = request.POST.getlist('site_name')
        salt_command = {
            "title":title,
            "ticket_type":ticket_type,
            "site_name":site_name,
            "handler":handler,
            "owner":owner
        }
    try:
        salt_command = json.dumps(salt_command)
        ticket_type = TicketType.objects.get(type_name=ticket_type)
        handler = User.objects.get(username=handler)
        task_id = str(uuid.uuid1())
        TicketTasks.objects.create(tasks_id=task_id,title=title,ticket_type=ticket_type,creator=request.user,content=salt_command,handler=handler,state='1')
        result = [{'TicketTasks':'The %s order submitted to success!' % (task_id)}]
        logs(user=request.user,ip=request.META['REMOTE_ADDR'],action='add ticket (%s)' % title,result='successful')
        user = User.objects.get(username=handler)
                
        phone_number = UserProfile.objects.get(user=user).phone_number  
        info = 'You have a message,please visit to workflow page.'
        dingding_robo(phone_number=phone_number,types=2,info=info)
    except Exception, e:
        print e
        result = [{'TicketTasks':'The order submitted to failed!'}]
        logs(user=request.user,ip=request.META['REMOTE_ADDR'],action='add ticket (%s)' % title,result='failed')
    
    return render(request,'getdata.html',{'result':result})    
        
        


@login_required
@deny_resubmit(page_key='handle_tickets')
def handle_tickets(request):
    task_id = request.POST['id']
    submit = request.POST['submit']
    reply = request.POST['reply']
    operating_id = TicketTasks.objects.get(tasks_id=task_id)
    content = TicketTasks.objects.get(tasks_id=task_id).content
    content = json.loads(content)
    username = User.objects.get(username=content['handler'])
    phone_number = UserProfile.objects.get(user=username).phone_number  
    handle_result = 0

    if submit == 'reject':
        TicketTasks.objects.filter(tasks_id=task_id).update(state='4')
        TicketOperating.objects.create(operating_id=operating_id,handler=username,content=reply,result='2',submitter=content['owner'])
        
        logs(user=request.user,ip=request.META['REMOTE_ADDR'],action='handle ticket (%s)' % content['title'],result='successful')
        info = 'Your "%s" order be reject,please visit to workflow page.' % content['title']
        owner = User.objects.get(username=content['owner'])
        owner_phone_number = UserProfile.objects.get(user=owner).phone_number
        dingding_robo(phone_number=owner_phone_number,types=2,info=info)
        result = [{'HandleTasks':'The task_id handle to success!'}]
        return render(request,'getdata.html',{'result':result}) 

    if content['ticket_type'] == 'go':
        #'----------------------------ticket_type--------------------'
        for host in content['hosts']:
            data = {
                'client':'local',
                'tgt':host,
                'fun':'state.sls',
                'arg':['goservices.supervisor_submodule','pillar={"goprograme":"%s","svnrepo":"%s","supProgrameName":"%s","goRunCommand":"%s"}' % (content['project'],content['svn_repo'],content['supervisor_name'],content['go_command'])]
            }
            result = salt_api.salt_cmd(data)
            try:
                minion_host = minion.objects.get(saltname=host)    
                supervisor_info = gostatus.objects.get(hostname=minion_host)
                supervisor_obj = xmlrpclib.Server('http://%s:%s@%s:%s/RPC2' % (
                    supervisor_info.supervisor_username, supervisor_info.supervisor_password,
                    supervisor_info.supervisor_host, supervisor_info.supervisor_port))
                if supervisor_obj.supervisor.getProcessInfo(content['supervisor_name']):
                    deploy_result = 1
                    print '-------successful-----'
            except Exception, e:
                print e
                deploy_result = 0
                handle_result = 1
                TicketTasks.objects.filter(tasks_id=task_id).update(state='5')
                TicketOperating.objects.create(operating_id=operating_id,handler=username,content=reply,result='3',submitter=content['owner'])
                logs(user=request.user,ip=request.META['REMOTE_ADDR'],action='handle ticket (%s)' % content['title'],result='failed')
                info = 'The "%s" order is failed,please check in %s host.' % (content['title'],host)
                dingding_robo(phone_number=phone_number,types=2,info=info)
                result = [{'HandleTasks':'The task_id handle to failed!'}]
                print '------failed-------------'           
                return render(request,'getdata.html',{'result':result}) 
            
            #-------------------------new project-----------------------------------
            try:
                if deploy_result == 1:
                    if gogroup.objects.filter(name=content['project']):
                        print 'The %s project is existing!!' % content['project']
                    else:
                        obj = gogroup(name=content['project'])
                        obj.save()

                        project = gogroup.objects.get(name=content['project'])
                        obj = svn(username=svn_username,
                            password=svn_password,
                            repo=content['svn_repo'],
                            localpath=go_local_path + content['project'],
                            movepath=go_move_path + content['project'],
                            revertpath=go_revert_path,
                            executefile=go_local_path + content['project'] + '/' + content['project']
                            ,project=project)
                        obj.save()


                    #-------------------------gotemplate-----------------------------------
                    project = gogroup.objects.get(name=content['project'])
                    ip = minion_host.ip

                    if GOTemplate.objects.filter(hostname=minion_host).filter(project=project).filter(env=1):
                        print 'The %s gotemplate project is existing!!' % content['project']
                    else:
                        obj = GOTemplate(
                            username=svn_username,
                            password=svn_password,
                            repo=svn_gotemplate_repo,
                            localpath=svn_gotemplate_local_path,
                            env=1,
                            hostname=minion_host,
                            project=project)
                        obj.save()

                    #-------------------------goservices-----------------------------------
                    if goservices.objects.filter(saltminion=minion_host).filter(group=project).filter(name=content['supervisor_name']).filter(env=1):
                        print 'The %s goservice is existing!!' % content['supervisor_name']
                    else:
                        obj = goservices(
                            ip=ip,
                            name=content['supervisor_name'] ,
                            env=1,
                            group=project,
                            saltminion=minion_host,
                            owner=content['owner'],
                            has_statsd=content['statsd'],
                            has_sentry=content['sentry'],
                            comment=content['function'])
                        obj.save()                     
            except Exception, e:
                print e
                handle_result = 1
                TicketTasks.objects.filter(tasks_id=task_id).update(state='5')
                TicketOperating.objects.create(operating_id=operating_id,handler=username,content=reply,result='3',submitter=content['owner'])
                logs(user=request.user,ip=request.META['REMOTE_ADDR'],action='handle ticket (%s)' % content['title'],result='failed')
                result = [{'HandleTasks':'The task_id handle to failed!'}]
    elif content['ticket_type'] == 'webpage':
        try:
            data = {
                'client':'local',
                'tgt': webpage_host,
                'fun':'cmd.script',
                'arg':['salt://scripts/webpage.py','"%s"' % str(content['site_name'])] 
            }
            salt_api.salt_cmd(data)
        except Exception, e:
            print e
            handle_result = 1
            TicketTasks.objects.filter(tasks_id=task_id).update(state='5')
            TicketOperating.objects.create(operating_id=operating_id,handler=username,content=reply,result='3',submitter=content['owner'])
            logs(user=request.user,ip=request.META['REMOTE_ADDR'],action='handle ticket (%s)' % content['title'],result='failed')
            info = 'The "%s" order is failed,please check in %s host.' % (content['title'],host)
            dingding_robo(phone_number=phone_number,types=2,info=info)
            result = [{'HandleTasks':'The task_id handle to failed!'}]
    else:
        print '--------type is error...'
        handle_result = 1
        result = [{'HandleTasks':'The type is error!'}]
    if handle_result == 0:
            TicketTasks.objects.filter(tasks_id=task_id).update(state='3')
            TicketOperating.objects.create(operating_id=operating_id,handler=username,content=reply,result='1',submitter=content['owner'])
            logs(user=request.user,ip=request.META['REMOTE_ADDR'],action='handle ticket (%s)' % content['title'],result='successful')
            username = User.objects.get(username=content['owner'])            
            phone_number = UserProfile.objects.get(user=username).phone_number  
            info = 'Your "%s" order has been processed,please visit to workflow page.' % content['title']
            dingding_robo(phone_number=phone_number,types=2,info=info)
            result = [{'HandleTasks':'The task_id handle to success!'}]
    return render(request,'getdata.html',{'result':result}) 



@login_required
def handled_tasks(request):
    tasks = TicketOperating.objects.filter(
        Q(handler=request.user) | Q(submitter=request.user)
    ).order_by('-modify_time')
    return render(request,'handled_tasks.html',{'tasks':tasks})
    


