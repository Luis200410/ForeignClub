from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0007_seed_additional_courses"),
    ]

    operations = [
        migrations.CreateModel(
            name="ModuleStageProgress",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("stage_key", models.CharField(choices=[("launch-pad", "Launch Pad"), ("flight-deck", "Flight Deck"), ("afterburner", "Afterburner")], max_length=32)),
                ("completed_tasks", models.JSONField(blank=True, default=list)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("module", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="stage_progress", to="core.coursemodule")),
                ("profile", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="stage_progress", to="core.profile")),
            ],
            options={
                "verbose_name": "Module stage progress",
                "verbose_name_plural": "Module stage progress",
            },
        ),
        migrations.AddIndex(
            model_name="modulestageprogress",
            index=models.Index(fields=["profile", "module", "stage_key"], name="stage_progress_idx"),
        ),
        migrations.AlterUniqueTogether(
            name="modulestageprogress",
            unique_together={("profile", "module", "stage_key")},
        ),
    ]
