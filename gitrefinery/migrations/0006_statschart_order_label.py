# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gitrefinery', '0005_category_hidden'),
    ]

    operations = [
        migrations.AddField(
            model_name='statschartrelease',
            name='label',
            field=models.CharField(help_text='Label for this release in the chart (blank to use "repo: release")', blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='statschartrelease',
            name='order',
            field=models.IntegerField(help_text='Ordering index for this rule within the chart', default=0),
        ),
        migrations.AlterField(
            model_name='release',
            name='begin_rev',
            field=models.CharField(help_text='Beginning revision, e.g. origin/previous_branchname', max_length=80),
        ),
        migrations.AlterField(
            model_name='release',
            name='end_rev',
            field=models.CharField(help_text='Ending revision, e.g. origin/branchname', max_length=80),
        ),
    ]
