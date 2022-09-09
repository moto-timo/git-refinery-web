# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import re
import git

from django.db import migrations, models

def create_author_obj(apps, schema_editor):
    if not schema_editor.connection.alias == 'default':
        return
    Release = apps.get_model('gitrefinery', 'Release')
    Author = apps.get_model('gitrefinery', 'Author')

    for release in Release.objects.all():
        repo = git.Repo(release.repository.path)
        assert repo.bare == False
        for commit in release.commit_set.all():
            gitcommit = repo.commit(commit.revision)
            author, _ = Author.objects.get_or_create(name=gitcommit.author.name,
                                                    email=gitcommit.author.email)
            commit.author_obj = author
            commit.save()

class Migration(migrations.Migration):

    dependencies = [
        ('gitrefinery', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('email', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='AuthorGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='AuthorGroupMembership',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('author', models.ForeignKey(on_delete=models.deletion.CASCADE, to='gitrefinery.Author')),
                ('group', models.ForeignKey(on_delete=models.deletion.CASCADE, to='gitrefinery.AuthorGroup')),
            ],
        ),
        migrations.AddField(
            model_name='commit',
            name='author_obj',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, null=True, blank=True, to='gitrefinery.Author'),
        ),
        migrations.RunPython(create_author_obj),
    ]
