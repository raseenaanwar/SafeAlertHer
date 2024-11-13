# Generated by Django 5.1.3 on 2024-11-13 14:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_alert_ai_analysis_alert_safety_tips'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='alert',
            options={'ordering': ['-created_at']},
        ),
        migrations.AlterModelOptions(
            name='emergencycontact',
            options={'ordering': ['-created_at']},
        ),
        migrations.RemoveField(
            model_name='alert',
            name='ai_analysis',
        ),
        migrations.RemoveField(
            model_name='alert',
            name='safety_tips',
        ),
        migrations.AddField(
            model_name='emergencycontact',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='emergencycontact',
            name='phone',
            field=models.CharField(max_length=20),
        ),
        migrations.AlterField(
            model_name='emergencycontact',
            name='relationship',
            field=models.CharField(choices=[('PARENT', 'Parent'), ('SPOUSE', 'Spouse'), ('SIBLING', 'Sibling'), ('CHILD', 'Child'), ('RELATIVE', 'Relative'), ('FRIEND', 'Friend'), ('OTHER', 'Other')], max_length=20),
        ),
    ]