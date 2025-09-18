from __future__ import annotations

from django.db import migrations


COURSE_SPECS = [
    {
        "slug": "elementary-a2",
        "defaults": {
            "title": "Elementary A2 · Momentum English",
            "subtitle": "12-week system to build everyday flow",
            "summary": "Unlock confident daily interactions with structured support that keeps you speaking between labs.",
            "delivery_mode": "live",
            "difficulty": "foundation",
            "focus_area": "Momentum English",
            "fluency_level": "A2",
            "duration_weeks": 12,
            "weekly_commitment_hours": 4,
            "cohort_size": 16,
            "is_published": True,
        },
    },
    {
        "slug": "intermediate-b1",
        "defaults": {
            "title": "Intermediate B1 · Expression League",
            "subtitle": "12-week arc to own fast conversations",
            "summary": "Push past hesitation with high-energy missions and coaching that sharpen spontaneity.",
            "delivery_mode": "live",
            "difficulty": "intensive",
            "focus_area": "Expression",
            "fluency_level": "B1",
            "duration_weeks": 12,
            "weekly_commitment_hours": 4,
            "cohort_size": 14,
            "is_published": True,
        },
    },
    {
        "slug": "upper-intermediate-b2",
        "defaults": {
            "title": "Upper Intermediate B2 · Influence Lab",
            "subtitle": "12-week engine to lead in English",
            "summary": "Train persuasion, negotiation, and storytelling inside cinematic studio missions.",
            "delivery_mode": "live",
            "difficulty": "intensive",
            "focus_area": "Influence",
            "fluency_level": "B2",
            "duration_weeks": 12,
            "weekly_commitment_hours": 5,
            "cohort_size": 12,
            "is_published": True,
        },
    },
    {
        "slug": "advanced-c1",
        "defaults": {
            "title": "Advanced C1 · Command Studio",
            "subtitle": "12-week accelerator for executive precision",
            "summary": "Operate at native speed with executive coaching, strategic labs, and evidence-based feedback.",
            "delivery_mode": "live",
            "difficulty": "master",
            "focus_area": "Command",
            "fluency_level": "C1",
            "duration_weeks": 12,
            "weekly_commitment_hours": 5,
            "cohort_size": 10,
            "is_published": True,
        },
    },
    {
        "slug": "proficient-c2",
        "defaults": {
            "title": "Proficient C2 · Legacy Studio",
            "subtitle": "12-week lab to craft lasting impact",
            "summary": "Shape culture, mentor others, and perform under pressure with elite-level simulations.",
            "delivery_mode": "live",
            "difficulty": "master",
            "focus_area": "Legacy",
            "fluency_level": "C2",
            "duration_weeks": 12,
            "weekly_commitment_hours": 5,
            "cohort_size": 8,
            "is_published": True,
        },
    },
]


def create_courses(apps, schema_editor):
    Course = apps.get_model("core", "Course")
    CourseModule = apps.get_model("core", "CourseModule")

    placeholder_description = "Curriculum details will be unveiled soon."
    placeholder_outcome = "Expect mission briefs, live studios, and afterburner retention labs aligned to this stage."

    for spec in COURSE_SPECS:
        course, created = Course.objects.get_or_create(
            slug=spec["slug"], defaults=spec["defaults"]
        )
        if not created:
            for field, value in spec["defaults"].items():
                setattr(course, field, value)
            course.save()

        if course.modules.exists():
            continue

        modules = []
        for order in range(1, 13):
            modules.append(
                CourseModule(
                    course=course,
                    order=order,
                    title=f"Week {order} · Coming Soon",
                    description=placeholder_description,
                    outcomes=placeholder_outcome,
                    focus_keyword=f"Week {order}",
                )
            )
        CourseModule.objects.bulk_create(modules)


def delete_courses(apps, schema_editor):
    Course = apps.get_model("core", "Course")
    Course.objects.filter(slug__in=[spec["slug"] for spec in COURSE_SPECS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_seed_beginner_a1_course"),
    ]

    operations = [
        migrations.RunPython(create_courses, delete_courses),
    ]
