import gitlab
from jenkinsapi.jenkins import Jenkins
from mico.settings import gitlab_url,gitlab_private_token,jenkins_webhook_url
from mico.settings import jenkins_url,jenkins_username,jenkins_password

def existGitlabProject(project_name):
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
            return True
        else:
            return False
    else:
        print 'The project name is error.'
        return 'The project name is error.'
   

def jenkins_create_job(project):
    for url in jenkins_url:
        j = Jenkins(url,username=jenkins_username,password=jenkins_password)
        if not j.has_job(project):
            job = j.copy_job('compile_template',project)
            job.disable()
            job.enable()
        else:
            print 'The project is exist in jenkins.'
            return False
    return True




