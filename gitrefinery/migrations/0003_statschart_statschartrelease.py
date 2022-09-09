# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gitrefinery', '0002_authors'),
    ]

    operations = [
        migrations.CreateModel(
            name='StatsChart',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField(blank=True)),
                ('categories', models.CharField(max_length=250, help_text='Comma-separated list of category names to include')),
                ('notes', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='StatsChartRelease',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('chart', models.ForeignKey(on_delete=models.deletion.CASCADE, to='gitrefinery.StatsChart')),
                ('release', models.ForeignKey(on_delete=models.deletion.CASCADE, to='gitrefinery.Release')),
            ],
        ),
    ]
