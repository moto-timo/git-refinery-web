# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gitrefinery', '0006_statschart_order_label'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthorGroupMatchRule',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('email_regex', models.CharField(max_length=100, help_text="Regular expression to use to match an author's email address to this group", blank=True)),
                ('order', models.IntegerField(default=0, help_text='Ordering index for this rule (rules will be applied in ascending order)')),
                ('group', models.ForeignKey(on_delete=models.deletion.CASCADE, to='gitrefinery.AuthorGroup')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
    ]
