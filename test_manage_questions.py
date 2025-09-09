"""
Test script to verify the manage_questions template is working
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spist_school.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from assessments.models import Assessment

User = get_user_model()

def test_manage_questions_view():
    print("Testing manage_questions view...")
    
    client = Client()
    
    try:
        # Login as teacher
        teacher_user = User.objects.get(email='teacher@spist.edu')
        login_success = client.login(email='teacher@spist.edu', password='password123')
        
        if not login_success:
            print("❌ Teacher login failed")
            return False
            
        # Get an assessment
        assessments = Assessment.objects.filter(creator=teacher_user)
        if not assessments.exists():
            print("❌ No assessments found for teacher")
            return False
            
        assessment = assessments.first()
        
        # Test the manage_questions URL
        url = f'/assessments/{assessment.id}/questions/'
        response = client.get(url)
        
        if response.status_code == 200:
            print(f"✅ Manage questions view successful: {url}")
            print(f"✅ Template rendered without errors")
            return True
        else:
            print(f"❌ Manage questions view failed: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_manage_questions_view()
    if success:
        print("\n🎉 Manage questions template test passed!")
    else:
        print("\n❌ Manage questions template test failed!")
