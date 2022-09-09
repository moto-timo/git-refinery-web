# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gitrefinery', '0004_helptexts'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='hidden',
            field=models.BooleanField(help_text='Hide from individual commit selection', default=False),
        ),
    ]
