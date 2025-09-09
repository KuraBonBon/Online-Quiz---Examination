"""
Quick test to verify manage_questions template is working
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spist_school.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from assessments.models import Assessment
import json

User = get_user_model()

def test_manage_questions_endpoint():
    print("Testing manage_questions endpoint...")
    
    client = Client()
    
    try:
        # Login as teacher
        teacher_user = User.objects.get(email='teacher@spist.edu')
        client.force_login(teacher_user)
        print(f"✅ Logged in as: {teacher_user.get_full_name()}")
        
        # Get assessments
        assessments = Assessment.objects.filter(creator=teacher_user)
        print(f"✅ Found {assessments.count()} assessments")
        
        if assessments.exists():
            assessment = assessments.first()
            
            # Test the problematic URL
            url = f'/assessments/{assessment.id}/questions/'
            print(f"Testing URL: {url}")
            
            response = client.get(url)
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ SUCCESS: manage_questions template rendered without errors!")
                return True
            else:
                print(f"❌ ERROR: Status {response.status_code}")
                if hasattr(response, 'content'):
                    print("Response content preview:", str(response.content)[:200])
                return False
        else:
            print("❌ No assessments found for testing")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_manage_questions_endpoint()
    if success:
        print("\n🎉 Template syntax error has been FIXED!")
    else:
        print("\n❌ Template still has issues")
