from flask import Flask,request,jsonify
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mico.settings')
django.setup()
from asset.utils import goPublish,go_action
from asset.models import gogroup,goservices,minion,svn,goconf,GOTemplate
from django.contrib import auth
import functools
from django.db import connection
from django.contrib.auth.models import User
from mico.settings import consul_api
import requests



app = Flask(__name__)

def login_author(func):
    @functools.wraps(func)
    def login_wrapper(*args,**kwargs):
        try:
            usernmae = request.json.get('username')
            password = request.json.get('password')
        except:
            return jsonify({'result': 'username or password is error'})

        if auth.authenticate(username = usernmae,password = password) is not None:
            connection.close()
            if request.json.get('env') is None:
                env={'env':'1'}
            elif int(request.json.get('env')) not in [1, 2]:
                return jsonify({'result': 'The env not found.!!'})
            else:
                env={'env':request.json.get('env')}
            request.get_json().update(env)
            return func(*args,**kwargs)
        else:
            return jsonify({'result': 'username or password is error'})
    return login_wrapper


@app.route('/',methods=['POST'])
@login_author
def message():
    print request.json.get('env')
    return jsonify({'hi':'hello world!!'})

@app.route('/deploy',methods=['POST'])
@login_author
def deploy_go():
    env = request.json.get('env')
    project = request.json.get('project')
    sub_project = request.json.get('sub_project')
    username = request.json.get('username')
    password = request.json.get('password')
    tower_url = request.json.get('tower_url')
   
    try:
        ip = request.headers['X-Real-Ip']
    except Exception, e:
        print e
        ip = request.remote_addr


    if tower_url and tower_url.find("tower.im") == -1:
        return jsonify({'result': 'The tower_url is error.!!'})

    if project and sub_project and tower_url:
        try:
            if gogroup.objects.filter(name=project):
                if goservices.objects.filter(name=sub_project):
                    publish = goPublish(env)
                    result = publish.deployGo(project, sub_project, username, ip, tower_url, '')
                    connection.close()
                    print result
                    if result:
                        result = str(result)
                        if result.find('ERROR') > 0 or result.find('error') > 0 or result.find('Skip') > 0:
                            result = 'Failed'
                        else:
                            result = 'Successful'
                    else:
                        result = 'Failed'
                    return jsonify({'result': result})
                else:
                    connection.close()
                    result = "No " + sub_project + " project!!"
                    return jsonify({'result': result})
            else:
                connection.close()
                result = "No " + project + " project!!"
                return jsonify({'result': result})
        except Exception, e:
            connection.close()
            print e
            return jsonify({'result': 'the env value is error!!'})
    else:
        return jsonify({'result': 'argv is error!!!'})




@app.route('/api/subProject',methods=['POST'])
@login_author
def add_sub_project():
    hostname = request.json.get('hostname')
    project = request.json.get('project')
    sub_project_name = request.json.get('sub_project_name')
    username = request.json.get('username')
    password = request.json.get('password')
    env = request.json.get('env')
    owner = request.json.get('owner')
    has_statsd = request.json.get('has_statsd')
    has_sentry = request.json.get('has_sentry')
    comment = request.json.get('comment')



    if project and hostname and sub_project_name and owner and has_sentry and has_statsd and comment:
        try:
            saltminion = minion.objects.get(saltname=hostname)
            project = gogroup.objects.get(name=project)
            ip = saltminion.ip
            if goservices.objects.filter(saltminion=saltminion).filter(group=project).filter(name=sub_project_name).filter(env=env):
                connection.close()
                return jsonify({'result': 'The %s subproject is existing!!' % sub_project_name })
        except Exception, e:
            connection.close()
            print e
            return jsonify({'result': 'wrong hostname or project name!!'})

        try:
            obj = goservices(ip=ip,name=sub_project_name ,env=env,group=project,saltminion=saltminion,owner=owner,has_statsd=has_statsd,has_sentry=has_sentry,comment=comment)
            obj.save()
            connection.close()
            return jsonify({'result': 'added %s subproject is successful.!!' % sub_project_name })
        except Exception, e:
            connection.close()
            print e
            return jsonify({'result': 'added %s subproject was failed.!!' % sub_project_name })
    else:
        return jsonify({'result': 'argv is error!!!'})



@app.route('/api/newProject',methods=['POST'])
@login_author
def add_new_project():
    new_project = request.json.get('new_project')
    username = request.json.get('username')
    password = request.json.get('password')
    svn_username = request.json.get('svn_username')
    svn_password = request.json.get('svn_password')
    svn_repo = request.json.get('svn_repo')
    svn_root_path = request.json.get('svn_root_path')
    svn_move_path = request.json.get('svn_move_path')
    svn_revert_path = request.json.get('svn_revert_path')
    svn_execute_file = request.json.get('svn_execute_file')
    env = request.json.get('env')



    if new_project and svn_username and svn_password and svn_repo and svn_root_path and svn_move_path and svn_revert_path and svn_execute_file:
        try:
            if gogroup.objects.filter(name=new_project):
                connection.close()
                return jsonify({'result': 'The %s new project is existing!!' % new_project})
            else:
                ###added a group project
                obj = gogroup(name=new_project)
                obj.save()

                ###added an info for svn table
                project = gogroup.objects.get(name=new_project)
                obj = svn(username=svn_username,password=svn_password,
                          repo=svn_repo,localpath=svn_root_path,
                          movepath=svn_move_path,revertpath=svn_revert_path,
                          executefile=svn_execute_file,project=project)
                obj.save()
                connection.close()
                return jsonify({'result': 'added %s new subproject is successful!!' % new_project})
        except Exception, e:
            connection.close()
            print e
            return jsonify({'result': 'added %s new subproject is failed!!' % new_project})
    else:
        return jsonify({'result': 'argv is error!!!'})




@app.route('/api/goconf',methods=['POST'])
@login_author
def add_goconf():   ###added an info for goconf table
    username = request.json.get('username')
    password = request.json.get('password')
    svn_username = request.json.get('svn_username')
    svn_password = request.json.get('svn_password')
    svn_repo = request.json.get('svn_repo')
    svn_root_path = request.json.get('svn_root_path')
    project = request.json.get('project')
    hostname = request.json.get('hostname')
    env = request.json.get('env')

    if svn_username and svn_password and svn_repo and svn_root_path and project and hostname:
        try:
            hostname = minion.objects.get(saltname=hostname)
            project = gogroup.objects.get(name=project)
            if goconf.objects.filter(hostname=hostname).filter(project=project).filter(env=env):
                connection.close()
                return jsonify({'result': 'The %s project is existing!!' % project})
            else:
                obj = goconf(username=svn_username,password=svn_password,repo=svn_repo,localpath=svn_root_path,env=env,hostname=hostname,project=project)
                obj.save()
                connection.close()
                return jsonify({'result': 'added %s goconf is successful!!' % project})
        except Exception, e:
            connection.close()
            print e
            return jsonify({'result': 'wrong hostname or project name!!'})
    else:
        return jsonify({'result': 'argv is error!!!'})



@app.route('/api/goAction',methods=['POST'])
@login_author
def go_operation():    # go 'stop,start,restart' operation
    username = request.json.get('username')
    password = request.json.get('password')
    try:
        ip = request.headers['X-Real-Ip']
    except Exception, e:
        print e
        ip = request.remote_addr

    service = request.json.get('service')
    method = request.json.get('method')


    if username and password and service and method:
        if goservices.objects.filter(name=service) and method in ['stop','start','restart']:
            obj = go_action(service,username,ip)
            try:
                if method == 'stop':
                    result = obj.stop()
                elif method == 'start':
                    result = obj.start()
                elif method == 'restart':
                    result = obj.restart()
                connection.close()
            except Exception, e:
                connection.close()
                print e
                return jsonify({'result': 'Internal Server Error'})
            return jsonify({'result': result})
        else:
            connection.close()
            return jsonify({'result': 'service name or method name is error!'})
    else:
        return jsonify({'result': 'argv is error!!!'})


@app.route('/api/gotemplate',methods=['POST'])
@login_author
def add_gotemplate():   ###added an info for gotemplate table
    username = request.json.get('username')
    password = request.json.get('password')
    svn_username = request.json.get('svn_username')
    svn_password = request.json.get('svn_password')
    svn_repo = request.json.get('svn_repo')
    svn_root_path = request.json.get('svn_root_path')
    project = request.json.get('project')
    hostname = request.json.get('hostname')
    env = request.json.get('env')

    if svn_username and svn_password and svn_repo and svn_root_path and project and hostname:
        try:
            hostname = minion.objects.get(saltname=hostname)
            project = gogroup.objects.get(name=project)
            if GOTemplate.objects.filter(hostname=hostname).filter(project=project).filter(env=env):
                connection.close()
                return jsonify({'result': 'The %s project is existing!!' % project})
            else:
                obj = GOTemplate(username=svn_username,password=svn_password,repo=svn_repo,localpath=svn_root_path,env=env,hostname=hostname,project=project)
                obj.save()
                connection.close()
                return jsonify({'result': 'added %s gotemplate is successful!!' % project})
        except Exception, e:
            connection.close()
            print e
            return jsonify({'result': 'wrong hostname or project name!!'})
    else:
        return jsonify({'result': 'argv is error!!!'})


@app.route('/api/goserviceInfo',methods=['POST'])
@login_author
def goservice_info():
    try:
        phone_number = []
        service_name = request.json.get('service_name')
        service = goservices.objects.filter(name=service_name)[0].owner
        phones = service.split(',')
        for p in phones:
            try:
                phone_number.append(User.objects.get(username=p).userprofile.phone_number)
            except Exception, e:
                print e
        print '------',phone_number
        connection.close()
    except Exception, e:
        connection.close()
        print e
        return jsonify({'result': ''})
    return jsonify({'result':phone_number })


@app.route('/api/getConsulKV',methods=['POST'])
@login_author
def get_consul_kv():
    try:
        url = None
        location = request.json.get('location')
        key = request.json.get('key')
        for l,k in consul_api.items():
            if location == l and key:
                url = k + key
        if not url:
            return jsonify({'result': 'wrong location or key name!!'})
        headers = {'Accept': 'application/json'}
        result = requests.get('%s?raw=True' % url, headers=headers).content
        return jsonify({'result': result})
    except Exception,e:
        print e
        return jsonify({'result': 'Intranet error!!'})


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5001)




