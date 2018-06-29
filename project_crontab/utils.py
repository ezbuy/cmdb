# coding=utf-8
import commands

from asset import utils
from salt_api.api import SaltApi
salt_api = SaltApi()


def salt_run_sls(login_user, svnrepo, projectname, salt_hostname, login_ip):
    errcode = 0
    msg = 'ok'
    try:
        pillar = '''pillar=\"{'svnrepo': '%s', 'goprograme': '%s'}\"''' % (svnrepo, projectname)
        pull_svn_cmd = "salt " + salt_hostname + " state.sls queue=True goservices.pull_svn " + pillar
        print 'pull_svn_cmd : '
        print pull_svn_cmd
        s, result = commands.getstatusoutput(pull_svn_cmd)
        if result.find('Failed:    0') < 0:
            utils.logs(login_user, login_ip, 'pull svn ' + projectname, 'Failed')
            print 'result : '
            print result
            errcode = 501
            msg = u'salt执行不成功：\n'
            msg += result.split('\n')[0]
        else:
            utils.logs(login_user, login_ip, 'pull svn ' + projectname, 'Successful')
    except Exception as e:
        errcode = 500
        msg = u'salt执行失败'
    return errcode, msg
