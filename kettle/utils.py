from celery.task import task
from salt_api.api import SaltApi
from mico.settings import kettle_host,kettle_install_dir,kettle_svn_path

@task
def kettle_run(cmd_type,file_path):
    salt_api = SaltApi()
    file_path = kettle_svn_path + file_path
    if int(cmd_type) == 1:
        cmd = '%span.sh -file %s' % (kettle_install_dir,file_path)
    elif int(cmd_type) == 2:
	    cmd = '%skitchen.sh -file %s' % (kettle_install_dir,file_path)

    data = {
    	'client': 'local',
        'tgt': kettle_host,
        'fun': 'cmd.run',
        'arg': cmd
        }

    result = salt_api.salt_cmd(data)
    if result != 0:
    	result = result['return']
 
    return result

