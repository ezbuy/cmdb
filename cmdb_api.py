from flask import Flask,request,jsonify
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mico.settings')
django.setup()
from asset.utils import goPublish
from asset.models import gogroup,goservices
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
    ip = request.remote_addr
    if env is None:
        env = 1
    if login(username,password) == 0:
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


def login(username,password):
    user = auth.authenticate(username = username,password = password)
    if user is not None:
        return 0
    else:
        return 1



if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5001)




