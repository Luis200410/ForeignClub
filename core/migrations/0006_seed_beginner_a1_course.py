from __future__ import annotations

from django.db import migrations


BEGINNER_WEEKS = [
    {
        "order": 1,
        "title": "Week 1 · Starting Point",
        "theme": "Alphabet, numbers, basic greetings",
        "vocabulary": "hello, goodbye, please, thank you, yes, no, one–ten",
        "skill": "Pronunciation of English sounds; spelling names",
        "project": "Record a 30-second voice note introducing yourself",
    },
    {
        "order": 2,
        "title": "Week 2 · Me & My Name",
        "theme": "Introducing yourself",
        "vocabulary": "name, age, country, live, speak, student, friend",
        "skill": 'Verb "to be" (I am, you are, he/she is)',
        "project": 'Write a 4-sentence "About Me" note in Google Notebook',
    },
    {
        "order": 3,
        "title": "Week 3 · Family & Friends",
        "theme": "Talking about family",
        "vocabulary": "mother, father, brother, sister, family, friend, husband, wife",
        "skill": "Possessive adjectives (my, your, his, her)",
        "project": "Create a simple family tree with labels in English",
    },
    {
        "order": 4,
        "title": "Week 4 · Daily Routines",
        "theme": "Everyday life",
        "vocabulary": "wake up, eat, go, work, study, play, sleep, breakfast, lunch, dinner",
        "skill": "Present simple (I eat, She plays)",
        "project": "Write your daily schedule with times in English",
    },
    {
        "order": 5,
        "title": "Week 5 · Home & Classroom",
        "theme": "Where I live and study",
        "vocabulary": "house, room, table, chair, bed, pen, book, computer",
        "skill": "There is / There are",
        "project": "Take a photo of your room and label 5 things in English",
    },
    {
        "order": 6,
        "title": "Week 6 · Food & Drinks",
        "theme": "At the supermarket",
        "vocabulary": "water, bread, rice, milk, apple, coffee, chicken, fish",
        "skill": "Countable vs uncountable nouns (a/an/some)",
        "project": "Make a shopping list in English with 10 items",
    },
    {
        "order": 7,
        "title": "Week 7 · Time & Dates",
        "theme": "Telling time and days",
        "vocabulary": "Monday–Sunday, morning, afternoon, evening, today, tomorrow, yesterday, o’clock, half past",
        "skill": "Asking the time: ‘What time is it?’",
        "project": "Write your weekly routine with days and times",
    },
    {
        "order": 8,
        "title": "Week 8 · Weather & Seasons",
        "theme": "Talking about the weather",
        "vocabulary": "hot, cold, rainy, sunny, cloudy, windy, snow, season, spring, summer",
        "skill": "Adjectives + ‘It is…’ (It’s cold today.)",
        "project": "Record a 30-second weather report in English",
    },
    {
        "order": 9,
        "title": "Week 9 · Clothes & Shopping",
        "theme": "At the store",
        "vocabulary": "shirt, shoes, pants, dress, jacket, buy, cheap, expensive, size",
        "skill": "Asking for prices (‘How much is this?’)",
        "project": "Write a short dialogue: customer + shop assistant",
    },
    {
        "order": 10,
        "title": "Week 10 · Transport & Places",
        "theme": "Moving around the city",
        "vocabulary": "bus, train, taxi, car, bicycle, airport, station, street, map",
        "skill": "Prepositions of place (in, on, under, next to, near, behind)",
        "project": "Draw a simple city map with 5 places and describe directions in English",
    },
    {
        "order": 11,
        "title": "Week 11 · Health & Body",
        "theme": "At the doctor",
        "vocabulary": "head, arm, leg, stomach, sick, tired, doctor, medicine",
        "skill": "Can / can’t (I can walk, I can’t run)",
        "project": "Roleplay: patient and doctor (write 6 lines of dialogue)",
    },
    {
        "order": 12,
        "title": "Week 12 · Review & Survival Skills",
        "theme": "Everyday English survival kit",
        "vocabulary": "Review of all vocabulary from weeks 1–11",
        "skill": "Asking/answering basic questions",
        "project": "Record a 1-minute video introducing yourself, your family, your routine, and your city",
    },
]


def create_course(apps, schema_editor):
    Course = apps.get_model("core", "Course")
    CourseModule = apps.get_model("core", "CourseModule")
    CourseSession = apps.get_model("core", "CourseSession")

    defaults = {
        "title": "Beginner A1 · Survival English",
        "subtitle": "12-week mission to unlock confident everyday English",
        "summary": "Start speaking from instinct with a mission-driven curriculum designed for true beginners. Learn to introduce yourself, describe your life, handle daily situations, and survive in any English-speaking environment.",
        "delivery_mode": "live",
        "difficulty": "foundation",
        "focus_area": "Survival English",
        "fluency_level": "A1",
        "duration_weeks": 12,
        "weekly_commitment_hours": 4,
        "cohort_size": 18,
        "is_published": True,
    }

    course, created = Course.objects.get_or_create(slug="beginner-a1", defaults=defaults)

    if not created:
        for field, value in defaults.items():
            setattr(course, field, value)
        course.save()

    CourseSession.objects.filter(module__course=course).delete()
    CourseModule.objects.filter(course=course).delete()
    session_order_map = {
        "live": 1,
        "workshop": 2,
        "game": 3,
    }

    for week in BEGINNER_WEEKS:
        description = f"Theme: {week['theme']}\nSkill focus: {week['skill']}"
        outcomes = f"Vocabulary: {week['vocabulary']}\nMini-project: {week['project']}"

        module = CourseModule.objects.create(
            course=course,
            order=week["order"],
            title=week["title"],
            description=description,
            outcomes=outcomes,
            focus_keyword=f"Week {week['order']}",
        )

        CourseSession.objects.create(
            module=module,
            order=session_order_map["live"],
            title=f"Live Lab · {week['theme']}",
            session_type="lab",
            duration_minutes=60,
            description=f"Coach-led immersion session practicing {week['skill'].lower()} in real scenarios.",
        )
        CourseSession.objects.create(
            module=module,
            order=session_order_map["workshop"],
            title=f"Workshop · Vocabulary activation",
            session_type="workshop",
            duration_minutes=45,
            description=f"Interactive drills to internalise vocabulary: {week['vocabulary']}.",
        )
        CourseSession.objects.create(
            module=module,
            order=session_order_map["game"],
            title=f"Game Mission · {week['project']}",
            session_type="game",
            duration_minutes=30,
            description=f"Guided mission: {week['project']}.",
            resources=[
                {"label": "Mission brief", "detail": week['project']},
            ],
        )


def delete_course(apps, schema_editor):
    Course = apps.get_model("core", "Course")
    Course.objects.filter(slug="beginner-a1").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_profile_placement_fields"),
    ]

    operations = [
        migrations.RunPython(create_course, delete_course),
    ]
