from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from core.models import (
    Course,
    CourseModule,
    CourseSession,
    ModuleMeetingActivity,
    ModuleFlightDeckActivity,
    ModuleLaunchPadActivity,
    ModuleLaunchPadTask,
    ModuleAfterburnerActivity,
    ModuleGame,
    ModuleGameFlashcard,
)
from datetime import timedelta

class Command(BaseCommand):
    help = "Seeds the database with English course content"

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding English courses...")

        # We wrap each course creation in its own atomic block or just let them run.
        # If we want the whole thing atomic, keep it. But for debugging, maybe separate?
        # Let's keep it atomic but handle existence better.
        with transaction.atomic():
            self.create_business_english_course()
            self.create_conversation_mastery_course()

        self.stdout.write(self.style.SUCCESS("Successfully seeded courses!"))

    def create_business_english_course(self):
        course, created = Course.objects.get_or_create(
            slug="business-english-pro",
            defaults={
                "title": "Business English Professional",
                "subtitle": "Master the language of international business",
                "summary": "Elevate your career with high-impact communication skills for meetings, negotiations, and presentations.",
                "delivery_mode": Course.DeliveryMode.LIVE,
                "difficulty": Course.Difficulty.INTENSIVE,
                "focus_area": "Career & business impact",
                "fluency_level": "B2",
                "duration_weeks": 8,
                "weekly_commitment_hours": 4.5,
                "cohort_size": 12,
                "is_published": True,
                "start_date": timezone.now().date(),
                "end_date": timezone.now().date() + timedelta(weeks=8),
            }
        )
        if created:
            self.stdout.write(f"Created course: {course.title}")
        else:
            self.stdout.write(f"Course already exists: {course.title}")

        # Module 1: Effective Meetings
        module1, _ = CourseModule.objects.get_or_create(
            course=course,
            order=1,
            defaults={
                "title": "Mastering Meetings",
                "description": "Learn to lead and participate in meetings with authority and clarity.",
                "outcomes": "Lead meetings, interrupt politely, summarize key points.",
                "focus_keyword": "Meetings"
            }
        )

        # Launch Pad (Stage 1)
        launch_pad, _ = ModuleLaunchPadActivity.objects.get_or_create(
            module=module1,
            defaults={
                "title": "Meeting Prep",
                "description": "Get ready for the week's focus on meetings."
            }
        )
        launch_pad.ensure_default_tasks()

        # Live Session
        CourseSession.objects.get_or_create(
            module=module1,
            order=1,
            defaults={
                "title": "The Art of Interruption",
                "session_type": CourseSession.SessionType.LAB,
                "duration_minutes": 60,
                "description": "Practice polite interruption strategies in a simulated boardroom setting."
            }
        )

        # Flight Deck (Stage 2) Activities
        ModuleFlightDeckActivity.objects.get_or_create(
            module=module1,
            slot=ModuleFlightDeckActivity.Slot.SCHEDULER,
            defaults={
                "title": "Book Your Simulation",
                "description": "Schedule your live negotiation practice with a peer.",
                "link_label": "Book Now",
                "link_url": "https://calendly.com/example/negotiation"
            }
        )

        # Afterburner (Stage 3)
        ModuleAfterburnerActivity.objects.get_or_create(
            module=module1,
            slot=ModuleAfterburnerActivity.Slot.REAL_WORLD,
            defaults={
                "title": "The 5-Minute Pitch",
                "description": "Record a 5-minute pitch for a new product idea and submit it for review.",
                "goal": "Persuasion"
            }
        )
        
        # Meeting Activities
        activity, _ = ModuleMeetingActivity.objects.get_or_create(
            module=module1,
            title="Opening the Meeting",
            defaults={
                "description": "Standard phrases to start a meeting professionally.",
                "grammar_formula": "Let's get started / Shall we begin",
                "example": "Since everyone is here, let's get started."
            }
        )
        
        # Flashcards
        game, _ = ModuleGame.objects.get_or_create(
            module=module1,
            title="Business Vocabulary",
            game_type=ModuleGame.GameType.ADAPTIVE_FLASHCARDS
        )
        ModuleGameFlashcard.objects.get_or_create(game=game, word="Agenda", defaults={"meaning": "A list of items to be discussed at a formal meeting.", "order": 1})
        ModuleGameFlashcard.objects.get_or_create(game=game, word="Minutes", defaults={"meaning": "The written record of what was said at a meeting.", "order": 2})
        ModuleGameFlashcard.objects.get_or_create(game=game, word="Consensus", defaults={"meaning": "A general agreement.", "order": 3})


    def create_conversation_mastery_course(self):
        course, created = Course.objects.get_or_create(
            slug="conversation-mastery",
            defaults={
                "title": "Conversation Mastery",
                "subtitle": "Speak with confidence in any social situation",
                "summary": "From small talk to deep discussions, unlock your ability to connect with anyone.",
                "delivery_mode": Course.DeliveryMode.LIVE,
                "difficulty": Course.Difficulty.FOUNDATION,
                "focus_area": "Conversational agility",
                "fluency_level": "B1",
                "duration_weeks": 6,
                "weekly_commitment_hours": 3.0,
                "cohort_size": 15,
                "is_published": True,
                "start_date": timezone.now().date(),
                "end_date": timezone.now().date() + timedelta(weeks=6),
            }
        )
        if created:
            self.stdout.write(f"Created course: {course.title}")
        else:
            self.stdout.write(f"Course already exists: {course.title}")

        # Module 1: Small Talk
        module1, _ = CourseModule.objects.get_or_create(
            course=course,
            order=1,
            defaults={
                "title": "The Science of Small Talk",
                "description": "Break the ice and keep the conversation flowing naturally.",
                "outcomes": "Initiate conversations, use open-ended questions, exit gracefully.",
                "focus_keyword": "Socializing"
            }
        )

        # Launch Pad
        launch_pad, _ = ModuleLaunchPadActivity.objects.get_or_create(
            module=module1,
            defaults={
                "title": "Social Warm-up",
                "description": "Prepare for social interactions."
            }
        )
        launch_pad.ensure_default_tasks()

        # Live Session
        CourseSession.objects.get_or_create(
            module=module1,
            order=1,
            defaults={
                "title": "Cocktail Party Simulator",
                "session_type": CourseSession.SessionType.LAB,
                "duration_minutes": 60,
                "description": "Navigate a virtual room and practice starting conversations with strangers."
            }
        )
        
        # Flashcards
        game, _ = ModuleGame.objects.get_or_create(
            module=module1,
            title="Social Idioms",
            game_type=ModuleGame.GameType.ADAPTIVE_FLASHCARDS
        )
        ModuleGameFlashcard.objects.get_or_create(game=game, word="Break the ice", defaults={"meaning": "To do or say something to relieve tension or get conversation going.", "order": 1})
        ModuleGameFlashcard.objects.get_or_create(game=game, word="Hit it off", defaults={"meaning": "To be naturally friendly or well-suited.", "order": 2})
