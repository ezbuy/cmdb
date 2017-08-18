import gitlab
from jenkinsapi.jenkins import Jenkins
from mico.settings import gitlab_url,gitlab_private_token,jenkins_webhook_url
from mico.settings import jenkins_url,jenkins_username,jenkins_password
from mico.settings import svn_host
from salt_api.api import SaltApi

salt_api = SaltApi()

def existGitlabProject(project_name,uat_env):
    '''
    error code:
     1. sucessful.
     2. gitlab  project name is not exist.
     3. jenkins creating is error.
     4. svn repo creating is error.
     5. gitlab webhook creating is error.
    '''
    gl = gitlab.Gitlab(gitlab_url,gitlab_private_token)
    project = gl.projects.search(project_name)

    print '------------1---',project
    if len(project) > 0:
        if jenkins_create_job(project_name,uat_env):
            for info in project:
                print '-------info.name---',info.name
                if info.name == project_name:
                    print '-------ok-------'
                    project_id = info.id
                    #####webhook url is exist#######
                    hooks_list = gl.project_hooks.list(project_id=project_id)
                    print '----------hooks_list',hooks_list
                    try:
                        if uat_env in ['uat', 'uat_aws']:
                            jenkins_webhook_url[uat_env].append(jenkins_webhook_url['deploy'])
                            for hook in jenkins_webhook_url[uat_env]:
                                hook = hook + '/' + project_name
                                webhook_num = 0
                                print hook

                                ####if exist,pass###
                                for webhook in hooks_list:
                                    if webhook.url == hook:
                                        print '---------webhook_url=====:',hook
                                        webhook_num = 1
                                        break
                                ###if not exist,add a webhook url###
                                print '---------------webhook_num------:',webhook_num
                                if webhook_num == 0:
                                        print '---------creating_webhook--------'
                                        gl.project_hooks.create({
                                            'url': hook,
                                            'push_events': 1},
                                            project_id = project_id)
                    except Exception, e:
                        print e
                        return 5
                    print '---------create svn repo------------'
                    data = {
                        'client': 'local',
                        'tgt': svn_host,
                        'fun': 'cmd.script',
                        'arg': ['salt://scripts/create_svn.sh', project_name]
                    }
                    salt_result = salt_api.salt_cmd(data)
                    if salt_result['return'][0][svn_host]['stdout'] == 'ok':
                        print '-----create svn repo is sucessful.'
                        return 1
                    else:
                        tasks_info = 'Error creating svn repo,please tell ops..\n\n'
                        return 4
            return 1
        else:
            return 3
    else:
        print 'The project name is not exist.'
        return 2
   

def jenkins_create_job(project,uat_env):
    try:
        if uat_env in ['uat','uat_aws']:
            jenkins_url[uat_env].append(jenkins_url['deploy'])
            for url in jenkins_url[uat_env]:
                j = Jenkins(url, username=jenkins_username, password=jenkins_password)
                if not j.has_job(project):
                    job = j.copy_job('compile_template', project)
                    job.disable()
                    job.enable()
                else:
                    print 'The project is exist in jenkins.'
        else:
            print 'The uat env is not found.'
            return false
    except Exception, e:
        print e
        return false

    return True




