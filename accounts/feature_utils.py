"""
Utility for handling incomplete features with professional notifications.
This provides a clean way to show "feature coming soon" messages
instead of Django error pages.
"""

from django.contrib import messages
from django.shortcuts import redirect
from django.http import JsonResponse
from django.template.loader import render_to_string
from functools import wraps


class FeatureNotImplemented:
    """
    Centralized handler for features that are not yet implemented.
    Provides clean, professional notifications instead of error pages.
    """
    
    @staticmethod
    def show_notification(request, feature_name, redirect_url=None, is_ajax=False):
        """
        Show a professional notification for unimplemented features.
        
        Args:
            request: Django request object
            feature_name: Name of the feature (e.g., "Assessment taking")
            redirect_url: URL to redirect to (defaults to previous page)
            is_ajax: Whether this is an AJAX request
        """
        message = f"{feature_name} feature will be implemented soon."
        
        if is_ajax:
            return JsonResponse({
                'status': 'info',
                'message': message,
                'feature_name': feature_name
            })
        
        messages.info(request, message)
        
        if redirect_url:
            return redirect(redirect_url)
        
        # Try to redirect to the referring page, or home if no referrer
        return redirect(request.META.get('HTTP_REFERER', '/'))


def feature_not_implemented(feature_name, redirect_url=None):
    """
    Decorator for views that are not yet implemented.
    
    Usage:
    @feature_not_implemented("Assessment Taking")
    def take_assessment_view(request, assessment_id):
        pass  # This won't be executed
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            return FeatureNotImplemented.show_notification(
                request, 
                feature_name, 
                redirect_url,
                request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            )
        return wrapper
    return decorator


def check_feature_implementation(features_config):
    """
    Check which features are implemented vs not implemented.
    
    Args:
        features_config: Dict with feature names as keys and implementation status as values
        
    Returns:
        Dict with 'implemented' and 'not_implemented' lists
    """
    implemented = []
    not_implemented = []
    
    for feature, is_implemented in features_config.items():
        if is_implemented:
            implemented.append(feature)
        else:
            not_implemented.append(feature)
    
    return {
        'implemented': implemented,
        'not_implemented': not_implemented
    }


# Feature implementation status tracking
FEATURE_STATUS = {
    # Accounts features
    'User Registration': True,
    'User Login': True,
    'Profile Management': True,
    'Password Change': True,
    'Avatar Upload': True,
    
    # Assessment features
    'Assessment Creation': True,
    'Question Management': True,
    'Assessment Publishing': True,
    'Assessment Taking': True,  # NOW FULLY IMPLEMENTED ✅
    'Assessment Submission': True,  # NOW FULLY IMPLEMENTED ✅
    'Assessment Results': True,  # NOW FULLY IMPLEMENTED ✅
    'Auto Grading': True,  # NOW FULLY IMPLEMENTED ✅
    'Manual Grading': True,  # Ready for implementation
    
    # Course features
    'Course Management': True,
    'Course Enrollment': True,
    'Enrollment Management': True,
    'Course Offerings': True,
    'Bulk Enrollment': True,
    'Enrollment Codes': True,
    'Class Lists': True,
    
    # Analytics features
    'Analytics Dashboard': True,
    'Student Analytics': True,
    'Teacher Analytics': True,
    'Assessment Analytics': True,
    'System Analytics': True,
    'Report Generation': True,
    
    # Advanced features (not yet started)
    'Live Chat Support': False,
    'Video Conferencing': False,
    'Assignment Submissions': False,
    'Grade Book': False,
    'Academic Calendar': False,
    'Notifications System': False,
    'Mobile App': False,
    'API Integration': False,
    'LMS Integration': False,
    'Email Notifications': False,
    'SMS Notifications': False,
    'Attendance Tracking': False,
    'Time Table Management': False,
    'Library Management': False,
    'Fee Management': False,
    'Scholarship Management': False,
    'Student Portal': False,
    'Parent Portal': False,
    'Alumni Management': False,
    'Event Management': False,
    'Document Management': False,
    'Backup & Recovery': False,
    'Multi-language Support': False,
    'Accessibility Features': False,
    'Advanced Security': False,
}


def get_implementation_summary():
    """Get a summary of feature implementation status."""
    total_features = len(FEATURE_STATUS)
    implemented = sum(1 for status in FEATURE_STATUS.values() if status)
    not_implemented = total_features - implemented
    
    return {
        'total': total_features,
        'implemented': implemented,
        'not_implemented': not_implemented,
        'percentage': round((implemented / total_features) * 100, 1)
    }
