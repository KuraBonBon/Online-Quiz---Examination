from django.contrib import admin
from .models import Assessment, Question, Choice, CorrectAnswer, StudentAttempt, StudentAnswer

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'assessment_type', 'creator', 'status', 'created_at', 'questions_count']
    list_filter = ['assessment_type', 'status', 'created_at']
    search_fields = ['title', 'description', 'creator__username']
    readonly_fields = ['created_at', 'updated_at']
    
    def questions_count(self, obj):
        return obj.questions.count()
    questions_count.short_description = 'Questions'

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text_short', 'question_type', 'assessment', 'points', 'order']
    list_filter = ['question_type', 'assessment__assessment_type']
    search_fields = ['question_text', 'assessment__title']
    
    def question_text_short(self, obj):
        return obj.question_text[:50] + '...' if len(obj.question_text) > 50 else obj.question_text
    question_text_short.short_description = 'Question Text'

@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ['choice_text_short', 'question', 'is_correct', 'order']
    list_filter = ['is_correct', 'question__question_type']
    search_fields = ['choice_text', 'question__question_text']
    
    def choice_text_short(self, obj):
        return obj.choice_text[:30] + '...' if len(obj.choice_text) > 30 else obj.choice_text
    choice_text_short.short_description = 'Choice Text'

@admin.register(CorrectAnswer)
class CorrectAnswerAdmin(admin.ModelAdmin):
    list_display = ['answer_text_short', 'question', 'is_case_sensitive', 'order']
    list_filter = ['is_case_sensitive', 'question__question_type']
    search_fields = ['answer_text', 'question__question_text']
    
    def answer_text_short(self, obj):
        return obj.answer_text[:30] + '...' if len(obj.answer_text) > 30 else obj.answer_text
    answer_text_short.short_description = 'Answer Text'

@admin.register(StudentAttempt)
class StudentAttemptAdmin(admin.ModelAdmin):
    list_display = ['student', 'assessment', 'attempt_number', 'score', 'percentage', 'is_completed', 'started_at']
    list_filter = ['is_completed', 'is_passed', 'assessment__assessment_type']
    search_fields = ['student__username', 'assessment__title']
    readonly_fields = ['started_at', 'completed_at']

@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ['attempt', 'question', 'is_correct', 'points_earned']
    list_filter = ['is_correct', 'question__question_type']
    search_fields = ['attempt__student__username', 'question__question_text']
