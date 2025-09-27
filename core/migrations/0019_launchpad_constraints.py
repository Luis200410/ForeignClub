from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0018_launchpad_seed'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='modulelaunchpadtask',
            constraint=models.UniqueConstraint(
                fields=('module', 'order'),
                name='unique_launchpad_task_order_per_module',
            ),
        ),
        migrations.AddConstraint(
            model_name='modulelaunchpadtask',
            constraint=models.UniqueConstraint(
                fields=('activity', 'order'),
                name='unique_launchpad_task_order_per_activity',
                condition=models.Q(activity__isnull=False),
            ),
        ),
    ]
