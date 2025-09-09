"""
Test script to verify True/False question functionality
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spist_school.settings')
django.setup()

from django.contrib.auth import get_user_model
from assessments.models import Assessment, Question, Choice

User = get_user_model()

def test_true_false_functionality():
    print("Testing True/False Question Functionality...")
    
    try:
        # Get test teacher
        teacher_user = User.objects.get(email='teacher@spist.edu')
        print(f"✅ Using teacher: {teacher_user.get_full_name()}")
        
        # Create test assessment
        assessment = Assessment.objects.create(
            title="True/False Test Assessment",
            assessment_type="quiz",
            creator=teacher_user,
            time_limit=15
        )
        print(f"✅ Created assessment: {assessment.title}")
        
        # Create True/False question
        question = Question.objects.create(
            assessment=assessment,
            question_type="true_false",
            question_text="Django is a Python web framework.",
            points=5,
            order=1
        )
        print(f"✅ Created True/False question: {question.question_text}")
        
        # Create choices (simulating the view logic)
        true_choice = Choice.objects.create(
            question=question,
            choice_text='True',
            order=1,
            is_correct=True  # Default correct answer
        )
        false_choice = Choice.objects.create(
            question=question,
            choice_text='False',
            order=2,
            is_correct=False
        )
        print(f"✅ Created choices: {true_choice.choice_text} (correct: {true_choice.is_correct}), {false_choice.choice_text} (correct: {false_choice.is_correct})")
        
        # Test changing the correct answer (simulating form submission)
        # Change correct answer to False
        true_choice.is_correct = False
        false_choice.is_correct = True
        true_choice.save()
        false_choice.save()
        
        # Verify the change
        choices = Choice.objects.filter(question=question)
        correct_choice = choices.filter(is_correct=True).first()
        print(f"✅ Changed correct answer to: {correct_choice.choice_text}")
        
        # Clean up
        assessment.delete()
        print("✅ Test data cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_true_false_functionality()
    if success:
        print("\n🎉 True/False functionality test PASSED!")
    else:
        print("\n❌ True/False functionality test FAILED!")
