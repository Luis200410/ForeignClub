from django.db import migrations

DEFAULT_TASKS = [
    {
        "title": "NotebookLM briefing: theme overview",
        "description": "",
        "link_label": "Open NotebookLM",
        "link_url": "https://notebooklm.google.com/app",
    },
    {
        "title": "Vocabulary pack with pronunciation clips",
        "description": "",
        "link_label": "Open NotebookLM",
        "link_url": "https://notebooklm.google.com/app",
    },
    {
        "title": "Speaking drill: record a 30-second practice",
        "description": "",
        "link_label": "Open NotebookLM",
        "link_url": "https://notebooklm.google.com/app",
    },
    {
        "title": "Micro-quiz to check comprehension",
        "description": "",
        "link_label": "Open NotebookLM",
        "link_url": "https://notebooklm.google.com/app",
    },
    {
        "title": "Cultural insight drop",
        "description": "",
        "link_label": "Open NotebookLM",
        "link_url": "https://notebooklm.google.com/app",
    },
    {
        "title": "Mission reflection prompt",
        "description": "",
        "link_label": "Open NotebookLM",
        "link_url": "https://notebooklm.google.com/app",
    },
]


def seed_launchpad_activities(apps, schema_editor):
    CourseModule = apps.get_model('core', 'CourseModule')
    ModuleLaunchPadActivity = apps.get_model('core', 'ModuleLaunchPadActivity')
    ModuleLaunchPadTask = apps.get_model('core', 'ModuleLaunchPadTask')

    for module in CourseModule.objects.all():
        activity, _ = ModuleLaunchPadActivity.objects.get_or_create(
            module=module,
            defaults={
                'title': f"{module.title} · Launch Pad" if module.title else "Launch Pad",
                'description': '',
                'is_active': True,
            },
        )

        tasks_qs = ModuleLaunchPadTask.objects.filter(module=module).order_by('order', 'id')
        if tasks_qs.exists():
            for index, task in enumerate(tasks_qs, start=1):
                task.activity_id = activity.id
                if task.order != index:
                    task.order = index
                task.save(update_fields=['activity', 'order'])
            continue

        seed_tasks = []
        for index, config in enumerate(DEFAULT_TASKS, start=1):
            seed_tasks.append(
                ModuleLaunchPadTask(
                    activity_id=activity.id,
                    module_id=module.id,
                    order=index,
                    title=config.get('title', ''),
                    description=config.get('description', ''),
                    link_label=config.get('link_label', 'Open NotebookLM'),
                    link_url=config.get('link_url', ''),
                    is_active=True,
                )
            )
        if seed_tasks:
            ModuleLaunchPadTask.objects.bulk_create(seed_tasks)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_alter_modulelaunchpadtask_options_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_launchpad_activities, migrations.RunPython.noop),
    ]
