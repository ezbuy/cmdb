import gitlab
from jenkinsapi.jenkins import Jenkins
from mico.settings import gitlab_url,gitlab_private_token,jenkins_webhook_url
from mico.settings import jenkins_url,jenkins_username,jenkins_password
from mico.settings import svn_host
from salt_api.api import SaltApi

salt_api = SaltApi()

def existGitlabProject(project_name):
    '''
    error code:
     1. sucessful.
     2. gitlab  project name is not exist.
     3. jenkins creating is error.
     4. svn repo creating is error.
    '''
    gl = gitlab.Gitlab(gitlab_url,gitlab_private_token)
    project = gl.projects.search(project_name)
    print '------------1---',project
    if len(project) > 0:
        if jenkins_create_job(project_name):
            for info in project:
                if info.name == project_name:
                    project_id = info.id
                    for hook in jenkins_webhook_url:
                        gl.project_hooks.create({
                        'url': hook + '/' + project_name,
                        'push_events': 1},
                        project_id = project_id)

                    print '---------create svn repo------------'
                    data = {
                        'client': 'local',
                        'tgt': svn_host,
                        'fun': 'cmd.script',
                        'arg': ['salt://scripts/create_svn.sh', project_name]
                    }
                    salt_result = salt_api.salt_cmd(data)
                    print '-----------salt_result---',salt_result
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
   

def jenkins_create_job(project):
    for url in jenkins_url:
        j = Jenkins(url,username=jenkins_username,password=jenkins_password)
        if not j.has_job(project):
            job = j.copy_job('compile_template',project)
            job.disable()
            job.enable()
        else:
            print 'The project is exist in jenkins.'
    return True




