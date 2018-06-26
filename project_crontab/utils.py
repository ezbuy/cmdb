# coding=utf-8
import getopt
import commands
from crontab import CronTab

from asset import models as asset_models
from asset.utils import logs
from asset import models
from project_crontab import models
from salt_api.api import SaltApi
from mico.settings import svn_username, svn_password, go_local_path, svn_repo_url
salt_api = SaltApi()


class CronOperation(object):
    def __init__(self, login_user, login_ip):
        self.login_user = login_user
        self.login_ip = login_ip
        self.errcode = 0
        self.msg = 'ok'

    def salt_run_sls(self, svnrepo, projectname, salt_hostname):
        try:
            pillar = '''pillar=\"{'svnrepo': '%s', 'goprograme': '%s'}\"''' % (svnrepo, projectname)
            pull_svn_cmd = "salt " + salt_hostname + " state.sls queue=True goservices.supervisor_submodule " + pillar
            s, result = commands.getstatusoutput(pull_svn_cmd)
            if result.find('Failed:    0') < 0:
                logs(self.login_user, self.login_ip, 'add svn ' + projectname, 'Failed')
            else:
                logs(self.login_user, self.login_ip, 'add svn ' + projectname, 'Successful')
        except Exception as e:
            self.errcode = 500
            self.msg = u'salt执行失败'
        return self.errcode, self.msg

    def get_cron_list(self):
        crontab_objs = models.CrontabCmd.objects.all().order_by('-create_time')
        return crontab_objs

    def add_cron(self, minion_obj, cmd, frequency):
        salt_hostname = minion_obj.saltname
        project_name = cmd.strip().split(' ')[0]

        try:
            svn_obj = asset_models.crontab_svn.objects.get(project=project_name, hostname=minion_obj)
        except asset_models.crontab_svn.DoesNotExist:
            self.errcode = 500
            self.msg = u'Crontab Svn不存在'
            return self.errcode, self.msg
        else:
            # salt机器上拉svn目录
            repo = svn_repo_url + project_name
            self.salt_run_sls(repo, project_name, salt_hostname)

            # 创建Crontab CMD
            try:
                models.CrontabCmd.objects.get(svn=svn_obj, cmd=cmd, frequency=frequency)
            except models.CrontabCmd.DoesNotExist:
                path = svn_obj.localpath
                cmd_list = cmd.strip().split(' ')
                args_list = []
                opts_dict = {}
                if ' -' not in cmd:
                    # 没有参数的命令
                    auto_cmd = path + '/' + cmd
                else:
                    # 有参数的命令
                    options, args = getopt.getopt(cmd_list, "hc:f:d:s:n:")
                    for opt in args:
                        if opt.startswith('-'):
                            index = args.index(opt)
                            args_list = args[:index]
                            key_list = args[index::2]
                            value_list = args[index + 1::2]
                            opts_dict = dict(zip(key_list, value_list))
                            break
                    auto_cmd = path + '/' + ' '.join(args_list) + ' '

                log_path = '/var/log/' + project_name + '/'
                if opts_dict:
                    if '-d' in opts_dict.keys():
                        log_name = opts_dict['-d'].split('.')[0] + '.log'
                    elif '-c' in opts_dict.keys():
                        log_name = args_list[0] + '_conf.log'
                    else:
                        log_name = args_list[0] + '.log'

                    for k, v in opts_dict.items():
                        if k == '-c':
                            auto_cmd += k + ' ' + path + '/' + 'conf/' + v + ' '
                        elif k == '-d':
                            auto_cmd += k + ' ' + path + '/' + 'conf/' + v + ' '
                        else:
                            auto_cmd += k + ' ' + v + ' '

                    auto_cmd += '>> ' + log_path + log_name + ' 2>&1' + '\n'
                else:
                    log_name = '_'.join(cmd_list) + '.log'
                    auto_cmd += ' >> ' + log_path + log_name + ' 2>&1' + '\n'

                # 机器上创建
                # my_cron = CronTab(tabfile='/etc/crontab', user=False)
                # job = my_cron.new(command=auto_cmd, user='root')
                # job.setall(frequency.strip())
                # job.enable(False)
                # my_cron.write()

                # DB中创建
                models.CrontabCmd.objects.create(svn=svn_obj, cmd=cmd, auto_cmd=auto_cmd, frequency=frequency,
                                                 creator=self.login_user)
            else:
                self.errcode = 500
                self.msg = u'相同Crontab Cmd已存在'

        return self.errcode, self.msg

    def modify_cron(self, crontab_id):
        return self.errcode, self.msg

    def del_cron(self, del_cron_ids):
        cron_objs = models.CrontabCmd.objects.filter(id__in=del_cron_ids)
        # 在机器上暂停任务
        # my_cron = CronTab(tabfile='/etc/crontab', user=False)
        # for cron_obj in cron_objs:
        #     auto_cmd = cron_obj.auto_cmd.strip()
        #     print 'delCrontab---auto_cmd : '
        #     print auto_cmd
        #     for job in my_cron[4:]:
        #         if job.command == auto_cmd:
        #             job.enable(False)
        #             print 'delCrontab----disable---done'
        #             my_cron.write()
        #             break

        # 在DB中删除任务
        if len(cron_objs) == 0:
            self.errcode = 500
            self.msg = u'选中的项目在数据库中不存在'
        else:
            cron_objs.delete()

        return self.errcode, self.msg

    def start_cron(self, crontab_id):
        try:
            crontab_obj = models.CrontabCmd.objects.get(id=crontab_id)
        except models.CrontabCmd.DoesNotExist:
            self.errcode = 500
            self.msg = u'所选Crontab在数据库中不存在'
        else:
            # 修改机器上crontab状态为启动
            # my_cron = CronTab(tabfile='/etc/crontab', user=False)
            # auto_cmd = crontab_obj.auto_cmd.strip()
            # print 'startCrontab---auto_cmd : '
            # print auto_cmd
            # for job in my_cron[4:]:
            #     if job.command == auto_cmd:
            #         job.enable()
            #         print 'startCrontab----enable---done'
            #         my_cron.write()
            #         break

            # 修改数据库中cmd状态
            crontab_obj.cmd_status = 2
            crontab_obj.save()
        return self.errcode, self.msg

    def pause_cron(self, crontab_id):
        try:
            crontab_obj = models.CrontabCmd.objects.get(id=crontab_id)
        except models.CrontabCmd.DoesNotExist:
            errcode = 500
            msg = u'所选Crontab在数据库中不存在'
        else:
            # 修改机器上crontab状态为暂停
            # my_cron = CronTab(tabfile='/etc/crontab', user=False)
            # auto_cmd = crontab_obj.auto_cmd.strip()
            # print 'pauseCrontab---auto_cmd : '
            # print auto_cmd
            # for job in my_cron[4:]:
            #     if job.command == auto_cmd:
            #         job.enable(False)
            #         print 'pauseCrontab----disable---done'
            #         my_cron.write()
            #         break

            # 修改数据库中cmd状态
            crontab_obj.cmd_status = 1
            crontab_obj.save()
        return self.errcode, self.msg
