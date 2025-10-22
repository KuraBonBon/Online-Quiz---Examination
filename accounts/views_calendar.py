from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count
from django.core.paginator import Paginator
from datetime import datetime, timedelta, date
from calendar import monthrange
import json

from .models_calendar import CalendarEvent, EventCategory, UserCalendarSettings
from .forms_calendar import CalendarEventForm
from assessments.models import Assessment

@login_required
def calendar_view(request):
    """Main calendar view with month/week/day options"""
    # Get or create user calendar settings
    settings, created = UserCalendarSettings.objects.get_or_create(user=request.user)
    
    # Get view type from URL or user preference
    view_type = request.GET.get('view', settings.default_view)
    
    # Get current date or requested date
    today = timezone.now().date()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    day = int(request.GET.get('day', today.day))
    
    current_date = date(year, month, day)
    
    # Get events based on view type
    if view_type == 'month':
        events = get_month_events(request.user, year, month)
        calendar_data = generate_month_calendar(year, month, events)
        next_date = get_next_month(year, month)
        prev_date = get_prev_month(year, month)
    elif view_type == 'week':
        events = get_week_events(request.user, current_date)
        calendar_data = generate_week_calendar(current_date, events)
        next_date = current_date + timedelta(weeks=1)
        prev_date = current_date - timedelta(weeks=1)
    else:  # day view
        events = get_day_events(request.user, current_date)
        calendar_data = {'events': events, 'date': current_date}
        next_date = current_date + timedelta(days=1)
        prev_date = current_date - timedelta(days=1)
    
    # Get upcoming events for sidebar
    upcoming_events = get_upcoming_events(request.user, limit=5)
    
    # Get event categories for filtering
    categories = EventCategory.objects.filter(is_active=True)
    
    context = {
        'view_type': view_type,
        'current_date': current_date,
        'next_date': next_date,
        'prev_date': prev_date,
        'calendar_data': calendar_data,
        'upcoming_events': upcoming_events,
        'categories': categories,
        'settings': settings,
        'today': today,
    }
    
    return render(request, 'accounts/calendar/calendar_view.html', context)

@login_required
def calendar_api(request):
    """API endpoint for calendar events (AJAX)"""
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    categories = request.GET.getlist('categories[]')
    
    if not start_date or not end_date:
        return JsonResponse({'error': 'Start and end dates required'}, status=400)
    
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    
    # Get events in date range
    events_query = CalendarEvent.objects.filter(
        start_date__lte=end,
        end_date__gte=start,
        is_published=True
    ).select_related('category', 'created_by')
    
    # Filter by categories if specified
    if categories:
        events_query = events_query.filter(category__id__in=categories)
    
    # Filter by user visibility
    events = []
    for event in events_query:
        if event.is_visible_to_user(request.user):
            events.append({
                'id': event.id,
                'title': event.title,
                'start': event.start_date.isoformat(),
                'end': event.end_date.isoformat(),
                'color': event.category.color,
                'description': event.description,
                'location': event.location,
                'type': event.event_type,
                'priority': event.priority,
                'url': event.get_absolute_url(),
            })
    
    return JsonResponse(events, safe=False)

@login_required
def event_detail(request, pk):
    """Detailed view of a specific event"""
    event = get_object_or_404(CalendarEvent, pk=pk)
    
    # Check if user can view this event
    if not event.is_visible_to_user(request.user):
        messages.error(request, 'You do not have permission to view this event.')
        return redirect('accounts:calendar_view')
    
    # Check if user has permission to edit
    can_edit = (request.user.is_staff or 
                request.user == event.created_by or 
                request.user.user_type == 'admin')
    
    context = {
        'event': event,
        'can_edit': can_edit,
    }
    
    return render(request, 'accounts/calendar/event_detail.html', context)

@login_required
def create_event(request):
    """Create a new calendar event"""
    # Check permissions
    if not (request.user.is_staff or request.user.user_type in ['teacher', 'admin']):
        messages.error(request, 'You do not have permission to create events.')
        return redirect('accounts:calendar_view')
    
    # Pre-fill date if specified in URL
    selected_date = request.GET.get('date')
    initial_data = {}
    if selected_date:
        initial_data['start_date'] = selected_date
        initial_data['end_date'] = selected_date
    
    if request.method == 'POST':
        form = CalendarEventForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                event = form.save(commit=False)
                event.created_by = request.user
                event.save()
                form.save_m2m()  # Save many-to-many relationships
                
                messages.success(request, f'Event "{event.title}" created successfully!')
                return redirect('accounts:event_detail', pk=event.pk)
            except Exception as e:
                messages.error(request, f'Error creating event: {str(e)}')
        else:
            # Form has validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CalendarEventForm(initial=initial_data, user=request.user)
    
    context = {
        'form': form,
        'event_types': CalendarEvent.EVENT_TYPES,
        'priority_levels': CalendarEvent.PRIORITY_LEVELS,
    }
    
    return render(request, 'accounts/calendar/create_event.html', context)

@login_required
def edit_event(request, pk):
    """Edit an existing calendar event"""
    event = get_object_or_404(CalendarEvent, pk=pk)
    
    # Check permissions
    if not (request.user.is_staff or request.user == event.created_by or request.user.user_type == 'admin'):
        messages.error(request, 'You do not have permission to edit this event.')
        return redirect('accounts:event_detail', pk=pk)
    
    if request.method == 'POST':
        try:
            # Update event from form data
            event.title = request.POST['title']
            event.description = request.POST.get('description', '')
            event.category_id = request.POST['category']
            event.event_type = request.POST['event_type']
            event.start_date = request.POST['start_date']
            event.end_date = request.POST['end_date']
            event.start_time = request.POST.get('start_time') or None
            event.end_time = request.POST.get('end_time') or None
            event.is_all_day = request.POST.get('is_all_day') == 'on'
            event.location = request.POST.get('location', '')
            event.meeting_link = request.POST.get('meeting_link', '')
            event.audience = request.POST['audience']
            event.priority = request.POST['priority']
            
            # Handle specific courses and year levels
            if event.audience == 'specific':
                if request.POST.get('specific_courses'):
                    course_ids = request.POST.getlist('specific_courses')
                    event.specific_courses.set(course_ids)
                else:
                    event.specific_courses.clear()
                
                event.specific_year_levels = request.POST.get('specific_year_levels', '')
            else:
                event.specific_courses.clear()
                event.specific_year_levels = ''
            
            # Link to assessment if specified
            assessment_id = request.POST.get('linked_assessment')
            event.linked_assessment_id = assessment_id if assessment_id else None
            
            event.save()
            
            messages.success(request, f'Event "{event.title}" updated successfully!')
            return redirect('accounts:event_detail', pk=event.pk)
            
        except Exception as e:
            messages.error(request, f'Error updating event: {str(e)}')
    
    # Get form data for rendering
    categories = EventCategory.objects.filter(is_active=True)
    assessments = Assessment.objects.filter(creator=request.user, status='published')
    
    context = {
        'event': event,
        'categories': categories,
        'assessments': assessments,
        'event_types': CalendarEvent.EVENT_TYPES,
        'priority_levels': CalendarEvent.PRIORITY_LEVELS,
        'audience_types': CalendarEvent.AUDIENCE_TYPES,
    }
    
    return render(request, 'accounts/calendar/edit_event.html', context)

@login_required
def delete_event(request, pk):
    """Delete a calendar event"""
    event = get_object_or_404(CalendarEvent, pk=pk)
    
    # Check permissions
    if not (request.user.is_staff or request.user == event.created_by or request.user.user_type == 'admin'):
        messages.error(request, 'You do not have permission to delete this event.')
        return redirect('accounts:event_detail', pk=pk)
    
    if request.method == 'POST':
        event_title = event.title
        event.delete()
        messages.success(request, f'Event "{event_title}" deleted successfully!')
        return redirect('accounts:calendar_view')
    
    return render(request, 'accounts/calendar/delete_event.html', {'event': event})

# Helper functions
def get_month_events(user, year, month):
    """Get events for a specific month"""
    start_date = date(year, month, 1)
    _, last_day = monthrange(year, month)
    end_date = date(year, month, last_day)
    
    events = CalendarEvent.objects.filter(
        start_date__lte=end_date,
        end_date__gte=start_date,
        is_published=True
    ).select_related('category', 'created_by')
    
    return [event for event in events if event.is_visible_to_user(user)]

def get_week_events(user, start_date):
    """Get events for a specific week"""
    # Get Monday of the week
    days_since_monday = start_date.weekday()
    monday = start_date - timedelta(days=days_since_monday)
    sunday = monday + timedelta(days=6)
    
    events = CalendarEvent.objects.filter(
        start_date__lte=sunday,
        end_date__gte=monday,
        is_published=True
    ).select_related('category', 'created_by')
    
    return [event for event in events if event.is_visible_to_user(user)]

def get_day_events(user, target_date):
    """Get events for a specific day"""
    events = CalendarEvent.objects.filter(
        start_date__lte=target_date,
        end_date__gte=target_date,
        is_published=True
    ).select_related('category', 'created_by').order_by('start_time', 'title')
    
    return [event for event in events if event.is_visible_to_user(user)]

def get_upcoming_events(user, limit=5):
    """Get upcoming events for sidebar"""
    today = timezone.now().date()
    events = CalendarEvent.objects.filter(
        start_date__gte=today,
        is_published=True
    ).select_related('category', 'created_by').order_by('start_date', 'start_time')[:limit*2]
    
    # Filter visible events and limit
    visible_events = [event for event in events if event.is_visible_to_user(user)]
    return visible_events[:limit]

def generate_month_calendar(year, month, events):
    """Generate calendar data for month view"""
    _, num_days = monthrange(year, month)
    first_day = date(year, month, 1)
    last_day = date(year, month, num_days)
    
    # Get first Monday of calendar display
    start_date = first_day - timedelta(days=first_day.weekday())
    
    # Generate 6 weeks of calendar
    calendar_weeks = []
    current_date = start_date
    for week in range(6):
        week_days = []
        for day in range(7):
            day_events = [e for e in events if e.start_date <= current_date <= e.end_date]
            week_days.append({
                'date': current_date,
                'events': day_events,
                'in_month': current_date.month == month,
                'is_today': current_date == timezone.now().date(),
            })
            current_date += timedelta(days=1)
        calendar_weeks.append(week_days)
    
    return {
        'weeks': calendar_weeks,
        'month': month,
        'year': year,
        'month_name': first_day.strftime('%B'),
    }

def generate_week_calendar(start_date, events):
    """Generate calendar data for week view"""
    # Get Monday of the week
    days_since_monday = start_date.weekday()
    monday = start_date - timedelta(days=days_since_monday)
    
    week_days = []
    for i in range(7):
        current_date = monday + timedelta(days=i)
        day_events = [e for e in events if e.start_date <= current_date <= e.end_date]
        week_days.append({
            'date': current_date,
            'events': day_events,
            'is_today': current_date == timezone.now().date(),
        })
    
    return {
        'days': week_days,
        'start_date': monday,
        'end_date': monday + timedelta(days=6),
    }

def get_next_month(year, month):
    """Get next month date"""
    if month == 12:
        return date(year + 1, 1, 1)
    return date(year, month + 1, 1)

def get_prev_month(year, month):
    """Get previous month date"""
    if month == 1:
        return date(year - 1, 12, 1)
    return date(year, month - 1, 1)


@login_required
def calendar_settings(request):
    """View for managing user calendar settings"""
    from .forms_calendar import UserCalendarSettingsForm
    
    # Get or create user settings
    settings, created = UserCalendarSettings.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserCalendarSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'Calendar settings updated successfully!')
            return redirect('accounts:calendar_settings')
    else:
        form = UserCalendarSettingsForm(instance=settings)
    
    return render(request, 'accounts/calendar/calendar_settings.html', {
        'form': form,
        'settings': settings
    })