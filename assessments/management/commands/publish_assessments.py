from django.core.management.base import BaseCommand
from assessments.models import Assessment

class Command(BaseCommand):
    help = 'Publish all draft assessments for testing'

    def handle(self, *args, **options):
        # Update all draft assessments to published
        updated = Assessment.objects.filter(status='draft').update(status='published')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully published {updated} assessments')
        )
        
        # List all assessments
        assessments = Assessment.objects.all()
        self.stdout.write('\nCurrent assessments:')
        for assessment in assessments:
            self.stdout.write(f'- {assessment.title} ({assessment.status}) - Questions: {assessment.questions.count()}')