# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gitrefinery', '0003_statschart_statschartrelease'),
    ]

    operations = [
        migrations.AlterField(
            model_name='categorisationrule',
            name='author_regex',
            field=models.CharField(help_text='Regex to match against the commit author', max_length=250, blank=True),
        ),
        migrations.AlterField(
            model_name='categorisationrule',
            name='body_regex',
            field=models.CharField(help_text='Regex to match against the commit message body', max_length=250, blank=True),
        ),
        migrations.AlterField(
            model_name='categorisationrule',
            name='category',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, to='gitrefinery.Category', null=True, help_text='Category to put the commit into if the rule matches', blank=True),
        ),
        migrations.AlterField(
            model_name='categorisationrule',
            name='order',
            field=models.IntegerField(help_text='Ordering index for this rule (rules will be applied in ascending order)', default=0),
        ),
        migrations.AlterField(
            model_name='categorisationrule',
            name='path_regex',
            field=models.CharField(help_text='Regex to match against a path modified by the commit', max_length=250, blank=True),
        ),
        migrations.AlterField(
            model_name='categorisationrule',
            name='shortlog_regex',
            field=models.CharField(help_text='Regex to match against the commit shortlog', max_length=250, blank=True),
        ),
        migrations.AlterField(
            model_name='categorisationrule',
            name='stop_on_match',
            field=models.BooleanField(help_text='If selected, and this rule matches for a commit, stop checking other rules for that commit', default=False),
        ),
        migrations.AlterField(
            model_name='categorisationrule',
            name='value',
            field=models.CharField(help_text='Value to set for the category if the rule matches', max_length=250, blank=True),
        ),
        migrations.AlterField(
            model_name='category',
            name='title',
            field=models.CharField(help_text='Title to show for the section in the release notes, blank to exclude from the notes', max_length=100, blank=True),
        ),
        migrations.AlterField(
            model_name='release',
            name='begin_rev',
            field=models.CharField(help_text='Beginning revision, e.g. origin/<previous branchname>', max_length=80),
        ),
        migrations.AlterField(
            model_name='release',
            name='branch',
            field=models.CharField(help_text='Branch name, without remote/ prefix', max_length=50),
        ),
        migrations.AlterField(
            model_name='release',
            name='end_rev',
            field=models.CharField(help_text='Ending revision, e.g. origin/<branchname>', max_length=80),
        ),
        migrations.AlterField(
            model_name='repository',
            name='commit_url',
            field=models.CharField(help_text='Web URL template for commits. {rev} will be substituted with the revision (hash) and {branch} will be substituted with the branch from the release.', max_length=255, blank=True),
        ),
    ]
