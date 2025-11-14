from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('inspections', '0005_alter_inspectionitem_passed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inspectionitem',
            name='passed',
            field=models.BooleanField(null=True, blank=True),
        ),
    ]
