# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2018-06-13 13:40
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('asset', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='memcache',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('env', models.IntegerField(blank=True, choices=[(1, '\u751f\u4ea7\u73af\u5883'), (2, '\u6d4b\u8bd5\u73af\u5883')], null=True, verbose_name='\u8fd0\u884c\u73af\u5883')),
                ('ip', models.GenericIPAddressField()),
                ('port', models.CharField(default=b'11211', max_length=32)),
                ('memcacheName', models.CharField(max_length=64, unique=True)),
                ('saltMinion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='asset.minion')),
            ],
        ),
    ]
