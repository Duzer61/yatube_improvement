# Generated by Django 2.2.16 on 2022-12-17 11:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0009_auto_20221217_1409'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.UniqueConstraint(fields=('user', 'author'), name='unique_follow'),
        ),
    ]
