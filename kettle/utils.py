from celery.task import task
from salt_api.api import SaltApi
from mico.settings import kettle_host,kettle_install_dir,kettle_svn_path,kettle_log_path
from asset.utils import logs,dingding_robo


@task
def kettle_run(user,ip,cmd_type,file_path,kettle_log_file,phone_number):
    salt_api = SaltApi()
    file_path = kettle_svn_path + file_path
    kettle_log_file = kettle_log_path + kettle_log_file

    if int(cmd_type) == 1:
        cmd = '%span.sh -file %s -logfile %s' % (kettle_install_dir,file_path,kettle_log_file)
    elif int(cmd_type) == 2:
        cmd = '%skitchen.sh -file %s -logfile %s' % (kettle_install_dir,file_path,kettle_log_file) 

    exists_file_cmd = 'ls %s' % file_path
    exists_file = {
        'client': 'local',
        'tgt': kettle_host,
        'fun': 'cmd.run',
        'arg': exists_file_cmd
    }

    file_result = salt_api.salt_cmd(exists_file)
    if file_result['return'][0][kettle_host] != file_path:
        logs(user,ip,cmd,'not %s file.' % file_path)
        dingding_robo(kettle_host,'kettle job','it is error',user,phone_number)
        return 0
   
    data = {
    	'client': 'local',
        'tgt': kettle_host,
        'fun': 'cmd.run',
        'arg': cmd
        }

    result = salt_api.salt_cmd(data)
    if result != 0:
    	result = result['return']
    
    logs(user,ip,cmd,'running')
    dingding_robo(kettle_host,'kettle job',result,user,phone_number)
    return result



