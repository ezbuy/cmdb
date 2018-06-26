# coding: utf-8

from django.db import models
from django.contrib.auth.models import User

from asset.models import minion, crontab_svn


class CrontabCmd(models.Model):
    """
    crontab命令信息
    """
    STATUS = (
        (1, U'暂停中'),
        (2, U'运行中'),
    )
    svn = models.ForeignKey(crontab_svn, verbose_name=u"Crontab所属SVN", related_name="svn_of_crontab")
    cmd = models.TextField(verbose_name=u"手动填入的命令", blank=False, null=False)
    auto_cmd = models.TextField(verbose_name=u"自动补全的命令", blank=False, null=False)
    frequency = models.CharField(max_length=16, verbose_name=u"执行频率", blank=False, null=False)
    cmd_status = models.IntegerField(choices=STATUS, default=1, verbose_name=u"状态")
    creator = models.ForeignKey(User, verbose_name=u"创建者", related_name="creator_of_crontab", default=1)
    create_time = models.DateTimeField(verbose_name=u"创建日期", auto_now_add=True, null=True, blank=True)
    updater = models.ForeignKey(User, verbose_name=u"最后更新者", related_name="updater_of_crontab", blank=True, null=True)
    update_time = models.DateTimeField(verbose_name=u"最后更新日期", auto_now=True, blank=True, null=True)
    last_run_result = models.CharField(max_length=16, verbose_name=u"上次执行结果", blank=True, null=True)
    last_run_time = models.DateTimeField(verbose_name=u"上次执行时间", blank=True, null=True)

    def __unicode__(self):
        return self.svn.project, self.auto_cmd, self.frequency

    class Meta:
        verbose_name = u"crontab命令"
        verbose_name_plural = verbose_name
