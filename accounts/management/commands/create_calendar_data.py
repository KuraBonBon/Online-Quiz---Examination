from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models_calendar import EventCategory, CalendarEvent
from datetime import date, datetime, timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Create initial calendar data for SPIST system'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating initial calendar data...'))
        
        # Create Event Categories
        categories_data = [
            {
                'name': 'Academic Events',
                'color': '#004d40',
                'icon': 'fas fa-graduation-cap',
                'description': 'Academic activities, ceremonies, and milestones'
            },
            {
                'name': 'Examinations',
                'color': '#ff9800',
                'icon': 'fas fa-clipboard-check',
                'description': 'Midterm, final exams, and major assessments'
            },
            {
                'name': 'Assessments',
                'color': '#2196f3',
                'icon': 'fas fa-tasks',
                'description': 'Quizzes, assignments, and regular assessments'
            },
            {
                'name': 'School Holidays',
                'color': '#4caf50',
                'icon': 'fas fa-calendar-day',
                'description': 'National holidays and school breaks'
            },
            {
                'name': 'Faculty Meetings',
                'color': '#9c27b0',
                'icon': 'fas fa-users',
                'description': 'Teacher meetings, workshops, and training'
            },
            {
                'name': 'School Activities',
                'color': '#f44336',
                'icon': 'fas fa-star',
                'description': 'Sports events, festivals, and extracurricular activities'
            },
            {
                'name': 'Deadlines',
                'color': '#ff5722',
                'icon': 'fas fa-clock',
                'description': 'Important deadlines for submissions and applications'
            }
        ]
        
        created_categories = []
        for cat_data in categories_data:
            category, created = EventCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')
            else:
                self.stdout.write(f'Category already exists: {category.name}')
            created_categories.append(category)
        
        # Get admin user for creating events
        try:
            admin_user = User.objects.filter(is_staff=True).first()
            if not admin_user:
                admin_user = User.objects.filter(user_type='admin').first()
            
            if not admin_user:
                self.stdout.write(self.style.WARNING('No admin user found. Creating events with first user...'))
                admin_user = User.objects.first()
            
            if not admin_user:
                self.stdout.write(self.style.ERROR('No users found in system. Cannot create sample events.'))
                return
                
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('No users found in system. Cannot create sample events.'))
            return
        
        # Sample events data
        today = date.today()
        events_data = [
            {
                'title': 'First Quarter Midterm Examinations',
                'description': 'Midterm examinations for all subjects in the first quarter of the academic year.',
                'category': created_categories[1],  # Examinations
                'event_type': 'examination',
                'start_date': today + timedelta(days=14),
                'end_date': today + timedelta(days=18),
                'priority': 'high',
                'audience': 'all',
                'location': 'Various Classrooms',
                'created_by': admin_user
            },
            {
                'title': 'Programming Fundamentals Quiz',
                'description': 'Weekly quiz covering loops, conditionals, and basic data structures.',
                'category': created_categories[2],  # Assessments
                'event_type': 'assessment',
                'start_date': today + timedelta(days=7),
                'end_date': today + timedelta(days=7),
                'start_time': datetime.strptime('10:00', '%H:%M').time(),
                'end_time': datetime.strptime('11:00', '%H:%M').time(),
                'priority': 'medium',
                'audience': 'students',
                'location': 'Computer Laboratory 1',
                'created_by': admin_user
            },
            {
                'title': 'Independence Day Holiday',
                'description': 'National holiday celebrating Philippine Independence Day.',
                'category': created_categories[3],  # School Holidays
                'event_type': 'holiday',
                'start_date': date(today.year, 6, 12),
                'end_date': date(today.year, 6, 12),
                'priority': 'medium',
                'audience': 'all',
                'is_all_day': True,
                'created_by': admin_user
            },
            {
                'title': 'Monthly Faculty Meeting',
                'description': 'Regular monthly meeting for all faculty members to discuss academic matters and school policies.',
                'category': created_categories[4],  # Faculty Meetings
                'event_type': 'meeting',
                'start_date': today + timedelta(days=21),
                'end_date': today + timedelta(days=21),
                'start_time': datetime.strptime('14:00', '%H:%M').time(),
                'end_time': datetime.strptime('16:00', '%H:%M').time(),
                'priority': 'high',
                'audience': 'teachers',
                'location': 'Faculty Conference Room',
                'created_by': admin_user
            },
            {
                'title': 'SPIST Science Fair 2024',
                'description': 'Annual science fair showcasing student research projects and innovations.',
                'category': created_categories[5],  # School Activities
                'event_type': 'activity',
                'start_date': today + timedelta(days=35),
                'end_date': today + timedelta(days=37),
                'priority': 'high',
                'audience': 'all',
                'location': 'SPIST Main Auditorium',
                'created_by': admin_user
            },
            {
                'title': 'Research Paper Submission Deadline',
                'description': 'Final deadline for submitting research papers for undergraduate thesis.',
                'category': created_categories[6],  # Deadlines
                'event_type': 'deadline',
                'start_date': today + timedelta(days=28),
                'end_date': today + timedelta(days=28),
                'start_time': datetime.strptime('23:59', '%H:%M').time(),
                'priority': 'critical',
                'audience': 'students',
                'specific_year_levels': '4',
                'location': 'Registrar Office',
                'created_by': admin_user
            },
            {
                'title': 'Welcome Assembly for New Students',
                'description': 'Orientation and welcome ceremony for newly enrolled students.',
                'category': created_categories[0],  # Academic Events
                'event_type': 'academic',
                'start_date': today + timedelta(days=3),
                'end_date': today + timedelta(days=3),
                'start_time': datetime.strptime('08:00', '%H:%M').time(),
                'end_time': datetime.strptime('10:00', '%H:%M').time(),
                'priority': 'high',
                'audience': 'students',
                'location': 'SPIST Gymnasium',
                'created_by': admin_user
            }
        ]
        
        # Create sample events
        created_events = 0
        for event_data in events_data:
            # Check if event already exists
            existing_event = CalendarEvent.objects.filter(
                title=event_data['title'],
                start_date=event_data['start_date']
            ).first()
            
            if not existing_event:
                # Handle special cases for past dates
                if event_data['start_date'] < today:
                    # Adjust dates for past events to make them future events
                    days_diff = (today - event_data['start_date']).days
                    event_data['start_date'] = today + timedelta(days=30 + days_diff)
                    if 'end_date' in event_data:
                        event_data['end_date'] = event_data['start_date'] + (event_data['end_date'] - event_data['start_date'])
                
                event = CalendarEvent.objects.create(**event_data)
                created_events += 1
                self.stdout.write(f'Created event: {event.title}')
            else:
                self.stdout.write(f'Event already exists: {event_data["title"]}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {len(created_categories)} categories and {created_events} events!'
            )
        )
        
        # Display summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write('CALENDAR DATA SUMMARY')
        self.stdout.write('='*50)
        self.stdout.write(f'Total Categories: {EventCategory.objects.count()}')
        self.stdout.write(f'Total Events: {CalendarEvent.objects.count()}')
        self.stdout.write(f'Upcoming Events: {CalendarEvent.objects.filter(start_date__gte=today).count()}')
        self.stdout.write('\nCalendar system is ready for use! 📅')