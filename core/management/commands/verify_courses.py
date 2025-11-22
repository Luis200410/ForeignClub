from django.core.management.base import BaseCommand
from core.models import Course, CourseModule, CourseSession, ModuleGameFlashcard

class Command(BaseCommand):
    help = "Verifies the seeded course content"

    def handle(self, *args, **kwargs):
        self.stdout.write("Verifying course content...")

        courses = Course.objects.all()
        self.stdout.write(f"Total Courses: {courses.count()}")
        for course in courses:
            self.stdout.write(f"- {course.title} ({course.slug})")
            modules = course.modules.all()
            self.stdout.write(f"  Modules: {modules.count()}")
            for module in modules:
                self.stdout.write(f"  - {module.title}")
                self.stdout.write(f"    Sessions: {module.sessions.count()}")
                self.stdout.write(f"    Games: {module.games.count()}")
                for game in module.games.all():
                    self.stdout.write(f"      - {game.title}: {game.flashcards.count()} flashcards")

        if courses.count() >= 2:
            self.stdout.write(self.style.SUCCESS("Verification Successful: Content found."))
        else:
            self.stdout.write(self.style.ERROR("Verification Failed: Not enough courses found."))
