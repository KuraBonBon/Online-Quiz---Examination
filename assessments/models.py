from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

class Assessment(models.Model):
    """Base model for both quizzes and exams"""
    ASSESSMENT_TYPES = (
        ('quiz', 'Quiz'),
        ('exam', 'Exam'),
    )
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    assessment_type = models.CharField(max_length=10, choices=ASSESSMENT_TYPES)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_assessments')
    
    # Time settings
    time_limit = models.PositiveIntegerField(
        null=True, blank=True, 
        help_text="Time limit in minutes (leave blank for no time limit)"
    )
    
    # Display settings
    show_correct_answers = models.BooleanField(
        default=False,
        help_text="Show correct answers to students after completion"
    )
    randomize_questions = models.BooleanField(
        default=False,
        help_text="Randomize question order for each student"
    )
    randomize_choices = models.BooleanField(
        default=False,
        help_text="Randomize answer choices for multiple choice questions"
    )
    
    # Attempt settings
    max_attempts = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Maximum number of attempts allowed per student"
    )
    
    # Grading settings
    passing_score = models.PositiveIntegerField(
        default=60,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Minimum percentage to pass"
    )
    
    # Status and dates
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    available_from = models.DateTimeField(null=True, blank=True)
    available_until = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_assessment_type_display()}: {self.title}"
    
    @property
    def total_points(self):
        return sum(question.points for question in self.questions.all())

class Question(models.Model):
    """Individual questions within an assessment"""
    QUESTION_TYPES = (
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('identification', 'Identification'),
        ('enumeration', 'Enumeration'),
        ('essay', 'Essay'),
    )
    
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='questions')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    question_text = models.TextField()
    points = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)
    
    # For enumeration questions
    expected_answers_count = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="For enumeration: number of expected answers"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"{self.assessment.title} - Q{self.order}: {self.question_text[:50]}..."

class Choice(models.Model):
    """Answer choices for multiple choice questions"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    choice_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.choice_text} ({'Correct' if self.is_correct else 'Incorrect'})"

class CorrectAnswer(models.Model):
    """Correct answers for identification, enumeration, and essay questions"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='correct_answers')
    answer_text = models.TextField()
    is_case_sensitive = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.question.question_text[:30]}... - {self.answer_text}"

class StudentAttempt(models.Model):
    """Records of student attempts at assessments"""
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assessment_attempts')
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='attempts')
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    score = models.PositiveIntegerField(null=True, blank=True)
    max_score = models.PositiveIntegerField(null=True, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    is_completed = models.BooleanField(default=False)
    is_passed = models.BooleanField(default=False)
    
    attempt_number = models.PositiveIntegerField(default=1)
    
    class Meta:
        unique_together = ['student', 'assessment', 'attempt_number']
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.student.first_name} - {self.assessment.title} (Attempt {self.attempt_number})"

class StudentAnswer(models.Model):
    """Individual answers submitted by students"""
    attempt = models.ForeignKey(StudentAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    
    # For multiple choice and true/false
    selected_choice = models.ForeignKey(Choice, on_delete=models.CASCADE, null=True, blank=True)
    
    # For identification, enumeration, and essay
    text_answer = models.TextField(blank=True, null=True)
    
    # For enumeration (multiple text answers)
    enumeration_answers = models.JSONField(default=list, blank=True)
    
    is_correct = models.BooleanField(null=True, blank=True)
    points_earned = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ['attempt', 'question']
    
    def __str__(self):
        return f"{self.attempt.student.first_name} - {self.question.question_text[:30]}..."
