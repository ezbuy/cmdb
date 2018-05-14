# coding: utf-8
from django.shortcuts import render,HttpResponse
from django.contrib.auth.decorators import login_required
from asset.utils import deny_resubmit,logs
from models import TicketType,TicketTasks,TicketOperating,WebInfo
from django.contrib.auth.models import User
from django.db.models import Q, Count
from salt_api.api import SaltApi
from asset.models import gogroup,svn,minion,GOTemplate,goservices,gostatus,UserProfile
from mico.settings import svn_username,svn_password,go_local_path,go_move_path,go_revert_path,svn_gotemplate_repo
from mico.settings import svn_gotemplate_local_path,webpage_host,svn_host,svn_repo_url,m_webpage_host
from mico.settings import salt_location
from asset.utils import dingding_robo
import json
import uuid
import xmlrpclib
from utils import existGitlabProject
import time
import os

salt_api = SaltApi()


# Create your views here.
@login_required
@deny_resubmit(page_key='submit_tickets')
def index(request):
    ticket_type = TicketType.objects.all()
    webInfo = WebInfo.objects.all().order_by('site_name')
    services = goservices.objects.values('name').annotate(dcount=Count('name')).order_by('name')
    return render(request,'workflow_index.html',{'ticket_type':ticket_type,'webInfo':webInfo, 'services': services})


@login_required
def get_svc_minions(request):
    svc = goservices.objects.filter(name=request.GET.get('name'))
    s = [str(i.saltminion) for i in svc]
    ms = minion.objects.exclude(saltname__in=s).order_by('saltname')
    m = [str(j) for j in ms]
    return HttpResponse(json.dumps(dict(m=m, s=s)))


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
    tasks_info = ''
    title = request.POST['title']
    ticket_type = request.POST['ticket_type']
    handler = request.POST['handler']
    owner = str(request.user)
    if ticket_type == 'go':
        function = request.POST['function']
        hosts = request.POST.getlist('hosts')
        project = request.POST['project']
        project = project.strip()
        go_command = request.POST['go_command']
        go_port = request.POST['go_port'].replace(' ','')
        supervisor_name = go_command.replace(" ", "_")
        svn_repo = svn_repo_url + project
        statsd = request.POST['statsd']
        sentry = request.POST['sentry']
        level = request.POST['level']
        go_command = go_command + " -c /srv/gotemplate/%s/conf.ctmpl" % project
        
        salt_command = {
            "title":title,
            "ticket_type":ticket_type,
            "function":function,
            "hosts":hosts,
            "project":project,
            "level":level,
            "svn_repo":svn_repo,
            "supervisor_name":supervisor_name,
            "go_command":go_command,
            "go_port": go_port,
            "statsd":statsd,
            "sentry":sentry,
            "handler":handler,
            "owner":owner
        }
        ## create svn repo address
        if not gogroup.objects.filter(name=project):
            data = {
                'client':'local',
                'tgt': svn_host,
                'fun':'cmd.script',
                'arg':['salt://scripts/create_svn.sh',project] 
            }
            salt_result = salt_api.salt_cmd(data)
            if salt_result['return'][0][svn_host]['stdout'] == 'ok':
                tasks_info = 'Your project svn_repo is %s.\n\n' % (svn_repo)
                
            else:
                tasks_info = 'Error creating svn repo(%s),please tell ops..\n\n' % (svn_repo)
        else:
            tasks_info = 'Your project svn_repo is %s.\n\n' % (svn_repo)




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
    elif ticket_type == 'uat_jenkins':
        print request.POST
        jenkins_name = request.POST['jenkins_name']
        uat_env = request.POST['uat_env']
        salt_command = {
            "title":title,
            "ticket_type":ticket_type,
            "uat_env": uat_env,
            "jenkins_name":jenkins_name,
            "handler":handler,
            "owner":owner
	    }
    elif ticket_type == 'offline_go':
        service_name = request.POST['service_name']
        salt_command = {
            'title': title,
            'ticket_type': ticket_type,
            'service_name': service_name,
            'handler': handler,
            'owner': owner,
        }
    elif ticket_type == 'migrate_go':
        service_name = request.POST['service_name_m']
        salt_command = {
            'title': title,
            'ticket_type': ticket_type,
            'service_name': service_name,
            'handler': handler,
            'owner': owner,
            'to_hosts': request.POST.getlist('to_hosts'),
            'from_hosts': request.POST.getlist('from_hosts'),
        }
    elif ticket_type == 'scale_go':
        service_name = request.POST['service_name_s']
        salt_command = {
            'title': title,
            'ticket_type': ticket_type,
            'service_name': service_name,
            'handler': handler,
            'owner': owner,
            'scale_hosts': request.POST.getlist('scale_hosts'),
        }
    try:
        salt_command = json.dumps(salt_command)
        ticket_type = TicketType.objects.get(type_name=ticket_type)
        handler = User.objects.get(username=handler)
        task_id = str(uuid.uuid1())
        TicketTasks.objects.create(tasks_id=task_id,title=title,ticket_type=ticket_type,creator=request.user,content=salt_command,handler=handler,state='1')
        tasks_info = tasks_info + 'The %s order submitted to success!' % task_id
        result = [{'TicketTasks':tasks_info}]
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
            try:
                if host.find(salt_location) > 0:
                    print '-----salt_location:',salt_location
                    salt_run = SaltApi(salt_location)
                else:
                    salt_run = SaltApi()
                data = {
                    'client':'local_async',
                    'tgt':host,
                    'fun':'state.sls',
                    'arg':['goservices.supervisor_submodule','pillar={"goprograme":"%s","svnrepo":"%s","supProgrameName":"%s","goRunCommand":"%s"}' % (content['project'],content['svn_repo'],content['supervisor_name'],content['go_command'])]
                }
                result = salt_run.salt_cmd(data)
                jid = result['return'][0]['jid']
                print '------jid------:',jid

                jid_data = {
                    'client':'runner',
                    'fun':'jobs.exit_success',
                    'jid': jid
                }
                tag = True
                while tag:
                    jid_result = salt_run.salt_cmd(jid_data)
                    print '----jid_result----',jid_result['return'][0][host]
                    if jid_result['return'][0][host]:
                        tag = False
                    else:
                        time.sleep(10)

                print '---jid_result-----',jid_result

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
                            repo=svn_gotemplate_repo + content['project'],
                            localpath=svn_gotemplate_local_path + content['project'],
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
                            comment=content['function'],
                            ports=content['go_port'],
                            level=content['level']
                        )
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
            hsg_site = []
            aws_site = []
            for site in content['site_name']:
                if WebInfo.objects.get(site_value=site).type == 1:
                    hsg_site.append(site)
                else:
                    aws_site.append(site)
            if hsg_site:
                data = {
                    'client':'local',
                    'expr_form':'list',
                    'tgt': webpage_host,
                    'fun':'cmd.script',
                    'arg': ['salt://scripts/webpage.py', '"%s"' % str(hsg_site)]
                }
                salt_api.salt_cmd(data)

            if aws_site:
                data = {
                    'client': 'local',
                    'expr_form': 'list',
                    'tgt': m_webpage_host,
                    'fun': 'cmd.script',
                    'arg': ['salt://scripts/webpage.py', '"%s"' % str(aws_site)]
                }
                salt_api.salt_cmd(data)

        except Exception, e:
            print e
            handle_result = 1
            TicketTasks.objects.filter(tasks_id=task_id).update(state='5')
            TicketOperating.objects.create(operating_id=operating_id,handler=username,content=reply,result='3',submitter=content['owner'])
            logs(user=request.user,ip=request.META['REMOTE_ADDR'],action='handle ticket (%s)' % content['title'],result='failed')
            info = 'The "%s" order is failed.' % (content['title'])
            dingding_robo(phone_number=phone_number,types=2,info=info)
            result = [{'HandleTasks':'The task_id handle to failed!'}]
    elif content['ticket_type'] == 'uat_jenkins':
        try:
            jenkins = existGitlabProject(content['jenkins_name'],content['uat_env'])
            print '-----jenkins---',jenkins
            if jenkins == 2:
                result = [{'HandleTasks': 'The project name is not exist.'}]
                handle_result = 1
            elif jenkins == 3:
                result = [{'HandleTasks': 'jenkins creating is error.'}]
                handle_result = 1
            elif jenkins == 4:
                result = [{'HandleTasks': 'svn repo creating is error.'}]
                handle_result = 1
            elif jenkins == 5:
                result = [{'HandleTasks': 'gitlab webhook creating is error.'}]
                handle_result = 1
        except Exception, e:
            print e
            handle_result = 1
            TicketTasks.objects.filter(tasks_id=task_id).update(state='5')
            TicketOperating.objects.create(operating_id=operating_id,handler=username,content=reply,result='3',submitter=content['owner'])
            logs(user=request.user,ip=request.META['REMOTE_ADDR'],action='handle ticket (%s)' % content['title'],result='failed')
            info = 'The "%s" order is failed.' % (content['title'])
            dingding_robo(phone_number=phone_number, types=2, info=info)
            result = [{'HandleTasks':'The task_id handle to failed!'}]
    elif content['ticket_type'] == 'offline_go':
        try:
            offline_go(content['service_name'])
            result = [{'HandleTasks': 'The task_id handled successfully!'}]
        except Exception as e:
            print e
            handle_result = 1
            TicketTasks.objects.filter(tasks_id=task_id).update(state='5')
            TicketOperating.objects.create(operating_id=operating_id, handler=username, content=reply, result='3', submitter=content['owner'])
            logs(user=request.user, ip=request.META['REMOTE_ADDR'], action='handle ticket (%s)' % content['title'], result='failed')
            result = [{'HandleTasks': 'The task_id handle to failed!'}]
    elif content['ticket_type'] == 'migrate_go':
        for host in content['to_hosts']:
            try:
                result = _online_go(content['service_name'], host)
                print '==> MIGRATE', result

                minion_host = minion.objects.get(saltname=host)
                supervisor_info = gostatus.objects.get(hostname=minion_host)
                supervisor_obj = xmlrpclib.Server('http://%s:%s@%s:%s/RPC2' % (
                    supervisor_info.supervisor_username, supervisor_info.supervisor_password,
                    supervisor_info.supervisor_host, supervisor_info.supervisor_port))
                if supervisor_obj.supervisor.getProcessInfo(content['service_name']):
                    print '-------successful-----'

                _update_record(content['service_name'], host)
            except Exception as e:
                print e
                TicketTasks.objects.filter(tasks_id=task_id).update(state='5')
                TicketOperating.objects.create(operating_id=operating_id, handler=username, content=reply, result='3',
                                               submitter=content['owner'])
                logs(user=request.user, ip=request.META['REMOTE_ADDR'], action='handle ticket (%s)' % content['title'],
                     result='failed')
                info = 'The "%s" order is failed,please check in %s host.' % (content['title'], host)
                dingding_robo(phone_number=phone_number, types=2, info=info)
                result = [{'HandleTasks': 'The task_id handle to failed!'}]
                print '------failed-------------'
                return render(request, 'getdata.html', {'result': result})

        for host in content['from_hosts']:
            try:
                offline_go(content['service_name'], host)
            except Exception as e:
                print e
                handle_result = 1
                TicketTasks.objects.filter(tasks_id=task_id).update(state='5')
                TicketOperating.objects.create(operating_id=operating_id, handler=username, content=reply, result='3',
                                               submitter=content['owner'])
                logs(user=request.user, ip=request.META['REMOTE_ADDR'], action='handle ticket (%s)' % content['title'],
                     result='failed')
                result = [{'HandleTasks': 'The task_id handle to failed!'}]
    elif content['ticket_type'] == 'scale_go':
        for host in content['scale_hosts']:
            try:
                result = _online_go(content['service_name'], host)
                print '==> SCALE', result

                minion_host = minion.objects.get(saltname=host)
                supervisor_info = gostatus.objects.get(hostname=minion_host)
                supervisor_obj = xmlrpclib.Server('http://%s:%s@%s:%s/RPC2' % (
                    supervisor_info.supervisor_username, supervisor_info.supervisor_password,
                    supervisor_info.supervisor_host, supervisor_info.supervisor_port))
                if supervisor_obj.supervisor.getProcessInfo(content['service_name']):
                    print '-------successful-----'

                _update_record(content['service_name'], host)
            except Exception as e:
                print e
                TicketTasks.objects.filter(tasks_id=task_id).update(state='5')
                TicketOperating.objects.create(operating_id=operating_id, handler=username, content=reply, result='3',
                                               submitter=content['owner'])
                logs(user=request.user, ip=request.META['REMOTE_ADDR'], action='handle ticket (%s)' % content['title'],
                     result='failed')
                info = 'The "%s" order is failed,please check in %s host.' % (content['title'], host)
                dingding_robo(phone_number=phone_number, types=2, info=info)
                result = [{'HandleTasks': 'The task_id handle to failed!'}]
                print '------failed-------------'
                return render(request, 'getdata.html', {'result': result})
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


# ****************************************************************************
#
# Offline Go Services
#
# ****************************************************************************
def _offline_go(name, super_host, super_port, super_user, super_pass):
    s = xmlrpclib.Server('http://%s:%s@%s:%s/RPC2' % (super_user, super_pass, super_host, super_port))

    # 1. stop process
    print '--> 1. stop process: %s@%s' % (name, super_host)
    try:
        s.supervisor.stopProcess(name)
    except Exception as e:
        print e

    # 2. remove process
    print '--> 2. remove process: %s@%s' % (name, super_host)
    try:
        s.supervisor.removeProcessGroup(name)
    except Exception as e:
        print e


def _offline_clean(name, salt_minion_hostname):
    # 3. remove config
    print '--> 3. remove config: %s@%s' % (name, salt_minion_hostname)
    basedir = '/etc/supervisord.d'
    data = {
        'client': 'local',
        'tgt': salt_minion_hostname,
        'fun': 'file.rename',
        'arg': [os.path.join(basedir, name+'.ini'), os.path.join(basedir, name+'.ini.offline')],
    }
    result = salt_api.salt_cmd(data)
    print result


def offline_go(name, host=None):
    if host is None:
        services = goservices.objects.filter(name=name)
    else:
        services = goservices.objects.filter(name=name, saltminion__saltname=host)

    for svc in services:
        _super = gostatus.objects.get(supervisor_host=svc.ip)
        _offline_go(name, _super.supervisor_host, _super.supervisor_port,
                    _super.supervisor_username, _super.supervisor_password)
        _offline_clean(name, svc.saltminion)

    print '--> 4. delete db record: %s%s' % (name, '' if host is None else '@' + host)
    services.delete()


def _online_go(name, host):
    svc = goservices.objects.filter(name=name).first()
    nvs = svn.objects.get(project=svc.group)

    if host.find(salt_location) > 0:
        print '-----salt_location:', salt_location
        salt_run = SaltApi(salt_location)
    else:
        salt_run = SaltApi()

    data = {
        'client': 'local_async',
        'fun': 'state.sls',
        'tgt': host,
        'arg': [
            'goservices.supervisor_submodule',
            'pillar={'
            '"goprograme":"%s",'
            '"svnrepo":"%s",'
            '"supProgrameName":"%s",'
            '"goRunCommand":"%s -c /srv/gotemplate/%s/conf.ctmpl"}' % (
                nvs.project, nvs.repo, name, ' '.join(name.split('_')), nvs.project
            )
        ]
    }
    result = salt_run.salt_cmd(data)
    jid = result['return'][0]['jid']
    print '------jid------:', jid

    jid_data = {
        'client': 'runner',
        'fun': 'jobs.exit_success',
        'jid': jid
    }
    while 1:
        jid_result = salt_run.salt_cmd(jid_data)
        print '----jid_result----', jid_result['return'][0][host]
        if jid_result['return'][0][host]:
            break
        else:
            time.sleep(10)

    print '---jid_result-----', jid_result
    return result


def _update_record(name, host):
    _svc = goservices.objects.filter(name=name).first()
    minion_host = minion.objects.get(saltname=host)
    project = _svc.group

    # -------------------------gotemplate-----------------------------------
    if GOTemplate.objects.filter(hostname=minion_host).filter(project=project).filter(env=1):
        print 'The %s gotemplate project is existing!!' % project.name
    else:
        obj = GOTemplate(
            username=svn_username,
            password=svn_password,
            repo=svn_gotemplate_repo + project.name,
            localpath=svn_gotemplate_local_path + project.name,
            env=1,
            hostname=minion_host,
            project=project)
        obj.save()

    # -------------------------goservices-----------------------------------
    if goservices.objects.filter(saltminion=minion_host).filter(group=project).filter(name=name).filter(env=1):
        print 'The %s goservice is existing!!' % name
    else:
        obj = goservices(
            ip=minion_host.ip,
            name=name,
            env=1,
            group=project,
            saltminion=minion_host,
            owner=_svc.owner,
            has_statsd=_svc.has_statsd,
            has_sentry=_svc.has_sentry,
            comment=_svc.comment,
            ports=_svc.ports,
            level=_svc.level
        )
        obj.save()
