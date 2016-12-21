from flask import Flask,request,jsonify
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mico.settings')
django.setup()
from asset.utils import goPublish
from asset.models import gogroup,goservices,minion
from django.contrib import auth



app = Flask(__name__)

@app.route('/',methods=['GET'])
def message():
    return jsonify({'hi':'hello world!!'})

@app.route('/deploy',methods=['POST'])
def deploy_go():
    env = request.json.get('env')
    project = request.json.get('project')
    sub_project = request.json.get('sub_project')
    username = request.json.get('username')
    password = request.json.get('password')
    #ip = request.remote_addr
    ip = request.headers['X-Real-Ip']


    env = deploy_env(env)
    if env == 0:
        return jsonify({'result': 'The env not found.!!'})

    try:
        if login(username,password) == 1:
            if env and project and sub_project and username and ip:
                if gogroup.objects.filter(name=project):
                    if goservices.objects.filter(name=sub_project) or sub_project == "all":
                        publish = goPublish(env)
                        result = publish.deployGo(project, sub_project, username, ip)
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
                        result = "No " + sub_project + " project!!"
                        return jsonify({'result': result})
                else:
                    result = "No " + project + " project!!"
                    return jsonify({'result': result})
            else:
                return jsonify({'result': 'argv is error!!!'})
        else:
            return jsonify({'result': 'username or password is error'})
    except Exception, e:
        print e
        return jsonify({'result': e})


@app.route('/subproject',methods=['POST'])
def add_sub_project():
    project = request.json.get('project')
    hostname = request.json.get('hostname')
    ip = request.json.get('ip')
    name = request.json.get('name')
    env = request.json.get('env')
    username = request.json.get('username')
    password = request.json.get('password')

    env = deploy_env(env)

    if env == 0:
        return jsonify({'result': 'The env not found.!!'})

    if login(username, password) == 1:
        try:
            saltminion = minion.objects.get(saltname=hostname)
            project = gogroup.objects.get(name=project)
            if goservices.objects.filter(saltminion=saltminion).filter(group=project).filter(name=name):
                return jsonify({'result': 'The %s subproject is existing!!' % name})
        except Exception, e:
            print e
            return jsonify({'result': 'wrong hostname or project name!!'})

        try:
            obj = goservices(ip=ip,name=name,env=env,group=project,saltminion=saltminion)
            obj.save()
            return jsonify({'result': 'added %s subproject is successful.!!' % name})
        except Exception, e:
            print e
            return jsonify({'result': 'added %s subproject was failed.!!' % name})
    else:
        return jsonify({'result': 'username or password is error'})


def login(username,password):
    user = auth.authenticate(username = username,password = password)
    if user is not None:
        return 1
    else:
        return 0

def deploy_env(env):
    if env is None:
        return 1
    elif int(env) not in [1, 2]:
        return 0
    else:
        return env


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5001)




