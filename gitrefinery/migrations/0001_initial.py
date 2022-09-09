# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CategorisationRule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('shortlog_regex', models.CharField(blank=True, max_length=250)),
                ('body_regex', models.CharField(blank=True, max_length=250)),
                ('path_regex', models.CharField(blank=True, max_length=250)),
                ('author_regex', models.CharField(blank=True, max_length=250)),
                ('value', models.CharField(blank=True, max_length=250)),
                ('stop_on_match', models.BooleanField(default=False)),
                ('order', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('title', models.CharField(blank=True, max_length=100)),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'verbose_name_plural': 'Categories',
            },
        ),
        migrations.CreateModel(
            name='Commit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('revision', models.CharField(max_length=80)),
                ('author', models.CharField(max_length=250)),
                ('authored_date', models.DateTimeField()),
                ('committed_date', models.DateTimeField()),
                ('shortlog', models.TextField(blank=True)),
                ('commit_message', models.TextField(blank=True)),
                ('files', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='CommitCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('note', models.TextField(blank=True)),
                ('category', models.ForeignKey(on_delete=models.deletion.CASCADE, to='gitrefinery.Category')),
                ('commit', models.ForeignKey(on_delete=models.deletion.CASCADE, to='gitrefinery.Commit')),
            ],
            options={
                'verbose_name_plural': 'Commit categories',
            },
        ),
        migrations.CreateModel(
            name='Release',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField(blank=True)),
                ('branch', models.CharField(max_length=50)),
                ('begin_rev', models.CharField(max_length=80)),
                ('end_rev', models.CharField(max_length=80)),
            ],
        ),
        migrations.CreateModel(
            name='Repository',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('path', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('commit_url', models.CharField(blank=True, max_length=255)),
            ],
            options={
                'verbose_name_plural': 'Repositories',
            },
        ),
        migrations.AddField(
            model_name='release',
            name='repository',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, to='gitrefinery.Repository'),
        ),
        migrations.AddField(
            model_name='commit',
            name='release',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, to='gitrefinery.Release'),
        ),
        migrations.AddField(
            model_name='category',
            name='repository',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, to='gitrefinery.Repository'),
        ),
        migrations.AddField(
            model_name='categorisationrule',
            name='category',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, null=True, to='gitrefinery.Category', blank=True),
        ),
        migrations.AddField(
            model_name='categorisationrule',
            name='repository',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, to='gitrefinery.Repository'),
        ),
    ]
