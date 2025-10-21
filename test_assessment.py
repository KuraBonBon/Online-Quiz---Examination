#!/usr/bin/env python
"""
Test script to validate the assessment taking functionality
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spist_school.settings')
django.setup()

from django.contrib.auth import get_user_model
from assessments.models import Assessment, Question, Choice, StudentAttempt

User = get_user_model()

def test_assessment_system():
    print("🧪 Testing Assessment System...")
    
    # Get a test student
    student = User.objects.filter(user_type='student').first()
    if not student:
        print("❌ No student found! Please create a student account first.")
        return False
    
    print(f"✅ Found student: {student.email}")
    
    # Get a published assessment
    assessment = Assessment.objects.filter(status='published').first()
    if not assessment:
        print("❌ No published assessment found!")
        return False
        
    print(f"✅ Found assessment: {assessment.title}")
    print(f"   - Questions: {assessment.questions.count()}")
    print(f"   - Status: {assessment.status}")
    
    # Check questions
    questions = assessment.questions.all()
    for i, question in enumerate(questions[:3], 1):  # Show first 3 questions
        print(f"   - Q{i}: {question.question_text[:50]}... ({question.question_type})")
        if question.question_type == 'multiple_choice':
            choices = question.choices.all()
            print(f"     Choices: {choices.count()}")
            for choice in choices:
                marker = "✓" if choice.is_correct else " "
                print(f"      [{marker}] {choice.choice_text}")
    
    # Check if student has existing attempts
    existing_attempts = StudentAttempt.objects.filter(
        student=student,
        assessment=assessment
    ).count()
    
    print(f"   - Existing attempts: {existing_attempts}")
    
    print("\n🎯 Assessment system is ready!")
    print(f"   Student can take assessment at: /assessments/{assessment.id}/take/")
    return True

if __name__ == "__main__":
    test_assessment_system()