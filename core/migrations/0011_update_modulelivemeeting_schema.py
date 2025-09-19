"""Update ModuleLiveMeeting to act as meeting options."""

import django.db.models.deletion
from django.db import migrations, models
from django.utils import timezone


def set_default_title(apps, schema_editor):
    ModuleLiveMeeting = apps.get_model("core", "ModuleLiveMeeting")
    for meeting in ModuleLiveMeeting.objects.filter(title=""):
        meeting.title = f"Live mission · Week {meeting.module.order}"
        meeting.save(update_fields=["title"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0010_modulelivemeetingsignup"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="modulelivemeeting",
            unique_together=set(),
        ),
        migrations.RemoveIndex(
            model_name="modulelivemeeting",
            name="module_live_meeting_idx",
        ),
        migrations.RemoveField(
            model_name="modulelivemeeting",
            name="profile",
        ),
        migrations.AlterModelOptions(
            name="modulelivemeeting",
            options={
                "ordering": ["scheduled_for"],
                "verbose_name": "Module live meeting option",
                "verbose_name_plural": "Module live meeting options",
            },
        ),
        migrations.AddField(
            model_name="modulelivemeeting",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="modulelivemeeting",
            name="title",
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.AlterField(
            model_name="modulelivemeeting",
            name="module",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="live_meeting_options",
                to="core.coursemodule",
            ),
        ),
        migrations.AddIndex(
            model_name="modulelivemeeting",
            index=models.Index(fields=["module", "scheduled_for"], name="module_live_meeting_idx"),
        ),
        migrations.RunPython(set_default_title, migrations.RunPython.noop),
    ]
