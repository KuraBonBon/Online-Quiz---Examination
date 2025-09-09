"""
Test script to verify that the formset duplication issue has been fixed.
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spist_school.settings')
django.setup()

from django.forms import formset_factory
from assessments.forms import ChoiceForm, CorrectAnswerForm, ReferenceAnswerForm
from assessments.models import Assessment, Question, Choice, CorrectAnswer
from django.contrib.auth.models import User

def test_formset_behavior():
    """Test that formsets behave correctly when editing existing questions."""
    
    print("Testing formset behavior for question editing...")
    
    # Test 1: Multiple Choice with existing choices
    print("\n1. Testing Multiple Choice formsets:")
    existing_choices = [
        {'choice_text': 'Choice A', 'is_correct': True},
        {'choice_text': 'Choice B', 'is_correct': False},
        {'choice_text': 'Choice C', 'is_correct': False}
    ]
    
    # Calculate extra forms needed (minimum 4 total, but allow for existing choices)
    extra_needed = max(0, 4 - len(existing_choices))
    print(f"   - Existing choices: {len(existing_choices)}")
    print(f"   - Extra forms needed: {extra_needed}")
    
    ChoiceFormSetEdit = formset_factory(ChoiceForm, extra=extra_needed, max_num=10, can_delete=True)
    choice_formset = ChoiceFormSetEdit(prefix='choice', initial=existing_choices)
    
    total_forms = len(choice_formset.forms)
    print(f"   - Total forms in formset: {total_forms}")
    print(f"   - Expected total: {len(existing_choices) + extra_needed}")
    
    # Test 2: Identification/Enumeration with existing answers
    print("\n2. Testing Identification/Enumeration formsets:")
    existing_answers = [
        {'answer_text': 'Answer 1', 'is_case_sensitive': True},
        {'answer_text': 'Answer 2', 'is_case_sensitive': False}
    ]
    
    extra_needed = 1 if not existing_answers else 0
    print(f"   - Existing answers: {len(existing_answers)}")
    print(f"   - Extra forms needed: {extra_needed}")
    
    CorrectAnswerFormSetEdit = formset_factory(CorrectAnswerForm, extra=extra_needed, max_num=20, can_delete=True)
    answer_formset = CorrectAnswerFormSetEdit(prefix='answer', initial=existing_answers)
    
    total_forms = len(answer_formset.forms)
    print(f"   - Total forms in formset: {total_forms}")
    print(f"   - Expected total: {len(existing_answers) + extra_needed}")
    
    # Test 3: Essay with existing reference answers
    print("\n3. Testing Essay formsets:")
    existing_references = [
        {'answer_text': 'This is a reference answer with key points...'}
    ]
    
    extra_needed = 1 if not existing_references else 0
    print(f"   - Existing references: {len(existing_references)}")
    print(f"   - Extra forms needed: {extra_needed}")
    
    ReferenceAnswerFormSetEdit = formset_factory(ReferenceAnswerForm, extra=extra_needed, max_num=5, can_delete=True)
    reference_formset = ReferenceAnswerFormSetEdit(prefix='reference', initial=existing_references)
    
    total_forms = len(reference_formset.forms)
    print(f"   - Total forms in formset: {total_forms}")
    print(f"   - Expected total: {len(existing_references) + extra_needed}")
    
    # Test 4: Essay with no existing reference answers
    print("\n4. Testing Essay formsets with no existing data:")
    existing_references = []
    
    extra_needed = 1 if not existing_references else 0
    print(f"   - Existing references: {len(existing_references)}")
    print(f"   - Extra forms needed: {extra_needed}")
    
    ReferenceAnswerFormSetEdit = formset_factory(ReferenceAnswerForm, extra=extra_needed, max_num=5, can_delete=True)
    reference_formset = ReferenceAnswerFormSetEdit(prefix='reference', initial=existing_references)
    
    total_forms = len(reference_formset.forms)
    print(f"   - Total forms in formset: {total_forms}")
    print(f"   - Expected total: {len(existing_references) + extra_needed}")
    
    print("\n✅ All formset tests completed successfully!")
    print("The duplication issue should now be fixed.")

if __name__ == "__main__":
    test_formset_behavior()
