# coding: utf-8

import datetime
from django.db import models
from django.contrib.auth.models import User



ASSET_ENV = (
    (1, U'生产环境'),
    (2, U'测试环境')
    )

ASSET_STATUS = (
    (1, u"已使用"),
    (2, u"未使用"),
    (3, u"报废")
    )

ASSET_TYPE = (
    (1, u"物理机"),
    (2, u"虚拟机"),
    (3, u"交换机"),
    (4, u"路由器"),
    (5, u"防火墙"),
    (6, u"Docker"),
    (7, u"其他")
    )


class gogroup(models.Model):
    name = models.CharField(max_length=32,verbose_name=u"go group name",unique=True)
    def __unicode__(self):
        return self.name

class AssetGroup(models.Model):
    GROUP_TYPE = (
        ('P', 'PRIVATE'),
        ('A', 'ASSET'),
    )
    name = models.CharField(max_length=80, unique=True)
    comment = models.CharField(max_length=160, blank=True, null=True)

    def __unicode__(self):
        return self.name


class IDC(models.Model):
    name = models.CharField(max_length=32, verbose_name=u'机房名称')
    bandwidth = models.CharField(max_length=32, blank=True, null=True, default='', verbose_name=u'机房带宽')
    linkman = models.CharField(max_length=16, blank=True, null=True, default='', verbose_name=u'联系人')
    phone = models.CharField(max_length=32, blank=True, null=True, default='', verbose_name=u'联系电话')
    address = models.CharField(max_length=128, blank=True, null=True, default='', verbose_name=u"机房地址")
    network = models.TextField(blank=True, null=True, default='', verbose_name=u"IP地址段")
    date_added = models.DateField(auto_now=True, null=True)
    operator = models.CharField(max_length=32, blank=True, default='', null=True, verbose_name=u"运营商")
    comment = models.CharField(max_length=128, blank=True, default='', null=True, verbose_name=u"备注")

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = u"IDC机房"
        verbose_name_plural = verbose_name


class Asset(models.Model):
    """
    asset modle
    """
    ip = models.CharField(max_length=8192, blank=True, null=True, verbose_name=u"主机IP")
    other_ip = models.CharField(max_length=255, blank=True, null=True, verbose_name=u"其他IP")
    hostname = models.CharField(unique=True, max_length=128, verbose_name=u"主机名")
    port = models.IntegerField(blank=True, null=True, verbose_name=u"端口号")
    group = models.ManyToManyField(AssetGroup, blank=True, verbose_name=u"所属主机组")
    username = models.CharField(max_length=16, blank=True, null=True, verbose_name=u"管理用户名")
    password = models.CharField(max_length=64, blank=True, null=True, verbose_name=u"密码")
    use_default_auth = models.BooleanField(default=True, verbose_name=u"使用默认管理账号")
    idc = models.ForeignKey(IDC, blank=True, null=True,  on_delete=models.SET_NULL, verbose_name=u'机房')
    mac = models.CharField(max_length=20, blank=True, null=True, verbose_name=u"MAC地址")
    remote_ip = models.CharField(max_length=16, blank=True, null=True, verbose_name=u'远控卡IP')
    brand = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'硬件厂商型号')
    cpu = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'CPU')
    memory = models.CharField(max_length=128, blank=True, null=True, verbose_name=u'内存')
    disk = models.CharField(max_length=1024, blank=True, null=True, verbose_name=u'硬盘')
    system_type = models.CharField(max_length=32, blank=True, null=True, verbose_name=u"系统类型")
    system_version = models.CharField(max_length=8, blank=True, null=True, verbose_name=u"系统版本号")
    system_arch = models.CharField(max_length=16, blank=True, null=True, verbose_name=u"系统平台")
    cabinet = models.CharField(max_length=32, blank=True, null=True, verbose_name=u'机柜号')
    position = models.IntegerField(blank=True, null=True, verbose_name=u'机器位置')
    number = models.CharField(max_length=32, blank=True, null=True, verbose_name=u'资产编号')
    status = models.IntegerField(choices=ASSET_STATUS, blank=True, null=True, default=1, verbose_name=u"机器状态")
    asset_type = models.CharField(max_length=32, blank=True, null=True, verbose_name=u"主机类型")
    env = models.IntegerField(choices=ASSET_ENV, blank=True, null=True, verbose_name=u"运行环境")
    sn = models.CharField(max_length=128, blank=True, null=True, verbose_name=u"SN编号")
    date_added = models.DateTimeField(auto_now=True, null=True)
    is_active = models.BooleanField(default=True, verbose_name=u"是否激活")
    comment = models.CharField(max_length=128, blank=True, null=True, verbose_name=u"备注")
    wan_ip = models.CharField(max_length=8192, blank=True, null=True, verbose_name=u"外网IP")

    def __unicode__(self):
        return self.ip


class AssetRecord(models.Model):
    asset = models.ForeignKey(Asset)
    username = models.CharField(max_length=30, null=True)
    alert_time = models.DateTimeField(auto_now_add=True)
    content = models.TextField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)


class minion(models.Model):
    saltname = models.CharField(max_length=32, verbose_name=u'salt minion name')
    ip = models.GenericIPAddressField()

    def __unicode__(self):
        return self.saltname


class cron_minion(models.Model):
    name = models.CharField(max_length=32, verbose_name=u'alias name show to users', blank=True, null=True)
    saltminion = models.ForeignKey(minion)

    def __unicode__(self):
        return self.name


class goservices(models.Model):
    ip = models.GenericIPAddressField()
    name = models.CharField(max_length=128, verbose_name=u'goservices services name')
    env = models.IntegerField(choices=ASSET_ENV, blank=True, null=True, verbose_name=u"运行环境")
    group = models.ForeignKey(gogroup)
    saltminion = models.ForeignKey(minion)
    owner = models.CharField(max_length=32)
    comment = models.CharField(max_length=256)
    has_statsd = models.CharField(max_length=256)
    has_sentry = models.CharField(max_length=256)
    ports = models.CharField(max_length=128, null=True, verbose_name=u'ports')
    level = models.CharField(max_length=128, null=True, verbose_name=u'level')
    def __unicode__(self):
        return self.name

class svn(models.Model):
    username = models.CharField(max_length=32)
    password = models.CharField(max_length=32)
    repo = models.CharField(max_length=128)
    localpath = models.CharField(max_length=64)
    movepath = models.CharField(max_length=64)
    revertpath = models.CharField(max_length=64)
    executefile = models.CharField(max_length=64)
    project = models.ForeignKey(gogroup)

    def __unicode__(self):
        return self.repo


class GoServiceRevision(models.Model):
    name = models.CharField(max_length=128, verbose_name=u'Go Service name')
    last_rev = models.IntegerField(verbose_name=u"goproject latest successful revision")
    gotemplate_last_rev =  models.IntegerField(verbose_name=u"gotemplate latest successful revision")
    last_clock = models.IntegerField(verbose_name=u"latest successful timestamp")

    def __unicode__(self):
        return self.name

# class GoTemplateRevision(models.Model):
#     name = models.CharField(max_length=128, verbose_name=u'Go Project')
#     last_rev = models.IntegerField(verbose_name=u"latest successful revision")
#     last_clock = models.IntegerField(verbose_name=u"latest successful timestamp")
#
#     def __unicode__(self):
#         return self.name


class goconf(models.Model):
    username = models.CharField(max_length=32)
    password = models.CharField(max_length=32)
    repo = models.CharField(max_length=128)
    localpath = models.CharField(max_length=64)
    env = models.IntegerField(choices=ASSET_ENV, blank=True, null=True, verbose_name=u"运行环境")
    project = models.ForeignKey(gogroup)
    hostname = models.ForeignKey(minion)

    def __unicode__(self):
        return self.repo


class gobuild(models.Model):
    env = models.IntegerField(choices=ASSET_ENV, blank=True, null=True, verbose_name=u"运行环境")
    hostname = models.ForeignKey(minion)


class gostatus(models.Model):
    hostname = models.ForeignKey(minion)
    supervisor_host = models.CharField(max_length=128,default='192.168.1.1')
    supervisor_username = models.CharField(max_length=64)
    supervisor_password = models.CharField(max_length=64)
    supervisor_port = models.CharField(max_length=128,default='9001')

    def __unicode__(self):
        return self.supervisor_host

class crontab_svn(models.Model):
    hostname = models.ForeignKey(minion,blank=True,null=True)
    minion_hostname = models.ForeignKey(cron_minion,blank=True,null=True)
    username = models.CharField(max_length=32)
    password = models.CharField(max_length=32)
    repo = models.CharField(max_length=128,default="http://svn.abc.com/svn/test")
    localpath = models.CharField(max_length=64,default='/srv/testsvn')
    project = models.CharField(max_length=64)

    def __unicode__(self):
        return self.project

class GOTemplate(models.Model):
    username = models.CharField(max_length=32)
    password = models.CharField(max_length=32)
    repo = models.CharField(max_length=128)
    localpath = models.CharField(max_length=64)
    env = models.IntegerField(choices=ASSET_ENV, blank=True, null=True, verbose_name=u"运行环境")
    project = models.ForeignKey(gogroup)
    hostname = models.ForeignKey(minion)

    def __unicode__(self):
        return self.repo

class UserProfile(models.Model):
    phone_number = models.CharField(max_length=11)
    user = models.OneToOneField(User)
