# Generated by Django 4.2.2 on 2023-06-28 17:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app01', '0008_alter_keyword_approval_percentage_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='keyword',
            name='status',
            field=models.CharField(choices=[('PROPOSED', 'Proposed'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected'), ('ALTERNATIVE', 'Alternative')], default='Proposed', max_length=20),
        ),
        migrations.AlterField(
            model_name='keyworddefinition',
            name='status',
            field=models.CharField(choices=[('PROPOSED', 'Proposed'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected'), ('ALTERNATIVE', 'Alternative')], default='Proposed', max_length=20),
        ),
        migrations.AlterField(
            model_name='question',
            name='status',
            field=models.CharField(choices=[('PROPOSED', 'Proposed'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected'), ('ALTERNATIVE', 'Alternative')], default='Proposed', max_length=20),
        ),
        migrations.AlterField(
            model_name='questiontag',
            name='status',
            field=models.CharField(choices=[('PROPOSED', 'Proposed'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected'), ('ALTERNATIVE', 'Alternative')], default='Proposed', max_length=20),
        ),
    ]
