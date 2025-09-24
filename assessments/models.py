from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.utils import timezone
from django.db.models import Q
import json
import uuid
import os

User = get_user_model()

class AssessmentTemplate(models.Model):
    """Reusable assessment templates for teachers"""
    ASSESSMENT_TYPES = (
        ('quiz', 'Quiz'),
        ('exam', 'Exam'),
    )
    
    DIFFICULTY_LEVELS = (
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
        ('mixed', 'Mixed'),
    )
    
    SUBJECT_CATEGORIES = (
        ('math', 'Mathematics'),
        ('science', 'Science'),
        ('english', 'English'),
        ('history', 'History'),
        ('programming', 'Programming'),
        ('general', 'General'),
        ('other', 'Other'),
    )
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assessment_templates')
    
    # Template settings
    assessment_type = models.CharField(max_length=10, choices=ASSESSMENT_TYPES)
    subject_category = models.CharField(max_length=20, choices=SUBJECT_CATEGORIES, default='general')
    difficulty_level = models.CharField(max_length=10, choices=DIFFICULTY_LEVELS, default='medium')
    
    # Default settings for assessments created from this template
    default_time_limit = models.PositiveIntegerField(null=True, blank=True)
    default_max_attempts = models.PositiveIntegerField(default=1)
    default_passing_score = models.PositiveIntegerField(default=60)
    default_randomize_questions = models.BooleanField(default=False)
    default_randomize_choices = models.BooleanField(default=False)
    default_show_correct_answers = models.BooleanField(default=False)
    
    # Template metadata
    is_public = models.BooleanField(default=False, help_text="Make template available to other teachers")
    usage_count = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-usage_count', '-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_assessment_type_display()})"

class QuestionBank(models.Model):
    """Centralized question repository for reuse across assessments"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='question_banks')
    
    subject_category = models.CharField(max_length=20, choices=AssessmentTemplate.SUBJECT_CATEGORIES, default='general')
    difficulty_level = models.CharField(max_length=10, choices=AssessmentTemplate.DIFFICULTY_LEVELS, default='medium')
    
    # Sharing settings
    is_public = models.BooleanField(default=False)
    shared_with = models.ManyToManyField(User, blank=True, related_name='shared_question_banks')
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.questions.count()} questions)"

class DocumentImport(models.Model):
    """Track document imports for assessments"""
    IMPORT_STATUS = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('needs_review', 'Needs Review'),
    )
    
    DOCUMENT_TYPES = (
        ('docx', 'Word Document (.docx)'),
        ('pdf', 'PDF Document (.pdf)'),
    )
    
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='document_imports')
    document = models.FileField(
        upload_to='imports/documents/',
        validators=[FileExtensionValidator(allowed_extensions=['docx', 'pdf'])]
    )
    document_type = models.CharField(max_length=10, choices=DOCUMENT_TYPES)
    
    # Import settings
    extract_questions = models.BooleanField(default=True)
    extract_answers = models.BooleanField(default=True)
    auto_categorize = models.BooleanField(default=True)
    
    # Processing results
    status = models.CharField(max_length=15, choices=IMPORT_STATUS, default='pending')
    questions_extracted = models.PositiveIntegerField(default=0)
    questions_with_answers = models.PositiveIntegerField(default=0)
    processing_log = models.JSONField(default=dict, blank=True)
    error_messages = models.TextField(blank=True)
    
    # Associated assessment
    created_assessment = models.ForeignKey('Assessment', on_delete=models.SET_NULL, null=True, blank=True)
    
    uploaded_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Import: {os.path.basename(self.document.name)} by {self.uploaded_by.get_full_name()}"

class Assessment(models.Model):
    """Enhanced assessment model with advanced features"""
    ASSESSMENT_TYPES = (
        ('quiz', 'Quiz'),
        ('exam', 'Exam'),
        ('practice', 'Practice Test'),
        ('survey', 'Survey'),
    )
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('scheduled', 'Scheduled'),
        ('archived', 'Archived'),
        ('suspended', 'Suspended'),
    )
    
    GRADING_METHODS = (
        ('automatic', 'Automatic'),
        ('manual', 'Manual'),
        ('mixed', 'Mixed'),
    )
    
    # Basic information
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    assessment_type = models.CharField(max_length=10, choices=ASSESSMENT_TYPES)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_assessments')
    
    # Enhanced categorization
    subject_category = models.CharField(max_length=20, choices=AssessmentTemplate.SUBJECT_CATEGORIES, default='general')
    difficulty_level = models.CharField(max_length=10, choices=AssessmentTemplate.DIFFICULTY_LEVELS, default='medium')
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags for organization")
    
    # Template and source information
    created_from_template = models.ForeignKey(AssessmentTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    created_from_import = models.ForeignKey(DocumentImport, on_delete=models.SET_NULL, null=True, blank=True)
    source_question_bank = models.ForeignKey(QuestionBank, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Time settings
    time_limit = models.PositiveIntegerField(
        null=True, blank=True, 
        help_text="Time limit in minutes (leave blank for no time limit)"
    )
    auto_submit = models.BooleanField(
        default=True,
        help_text="Automatically submit when time limit is reached"
    )
    
    # Display settings
    show_correct_answers = models.BooleanField(
        default=False,
        help_text="Show correct answers to students after completion"
    )
    show_correct_answers_after = models.DateTimeField(
        null=True, blank=True,
        help_text="Show correct answers after this date/time"
    )
    randomize_questions = models.BooleanField(
        default=False,
        help_text="Randomize question order for each student"
    )
    randomize_choices = models.BooleanField(
        default=False,
        help_text="Randomize answer choices for multiple choice questions"
    )
    questions_per_page = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(50)],
        help_text="Number of questions to display per page"
    )
    
    # Attempt settings
    max_attempts = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Maximum number of attempts allowed per student"
    )
    allow_review = models.BooleanField(
        default=True,
        help_text="Allow students to review their answers before submitting"
    )
    allow_backtrack = models.BooleanField(
        default=True,
        help_text="Allow students to go back to previous questions"
    )
    
    # Grading settings
    grading_method = models.CharField(max_length=15, choices=GRADING_METHODS, default='automatic')
    passing_score = models.PositiveIntegerField(
        default=60,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Minimum percentage to pass"
    )
    weighted_scoring = models.BooleanField(
        default=False,
        help_text="Use weighted scoring based on question difficulty"
    )
    partial_credit = models.BooleanField(
        default=False,
        help_text="Allow partial credit for partially correct answers"
    )
    
    # Scheduling and availability
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    available_from = models.DateTimeField(null=True, blank=True)
    available_until = models.DateTimeField(null=True, blank=True)
    late_submission_penalty = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage penalty for late submissions"
    )
    
    # Security settings
    require_lockdown_browser = models.BooleanField(default=False)
    disable_copy_paste = models.BooleanField(default=False)
    require_webcam = models.BooleanField(default=False)
    ip_restrictions = models.TextField(
        blank=True,
        help_text="Comma-separated list of allowed IP addresses/ranges"
    )
    
    # Notifications
    notify_on_submission = models.BooleanField(default=True)
    email_results = models.BooleanField(default=False)
    
    # Analytics and metadata
    total_points = models.PositiveIntegerField(default=0)
    estimated_duration = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Estimated completion time in minutes"
    )
    view_count = models.PositiveIntegerField(default=0)
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    average_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_accessed = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['creator', 'status']),
            models.Index(fields=['assessment_type', 'subject_category']),
            models.Index(fields=['available_from', 'available_until']),
        ]
    
    def __str__(self):
        return f"{self.get_assessment_type_display()}: {self.title}"
    
    @property
    def is_available(self):
        """Check if assessment is currently available"""
        now = timezone.now()
        if self.status != 'published':
            return False
        if self.available_from and now < self.available_from:
            return False
        if self.available_until and now > self.available_until:
            return False
        return True
    
    @property
    def total_questions(self):
        """Get total number of questions"""
        return self.questions.count()
    
    def update_statistics(self):
        """Update assessment statistics"""
        attempts = self.attempts.filter(is_completed=True)
        if attempts.exists():
            self.completion_rate = (attempts.count() / max(self.view_count, 1)) * 100
            scores = [attempt.percentage for attempt in attempts if attempt.percentage]
            if scores:
                self.average_score = sum(scores) / len(scores)
        self.save(update_fields=['completion_rate', 'average_score'])
    
    def calculate_total_points(self):
        """Calculate and update total points"""
        self.total_points = sum(question.points for question in self.questions.all())
        self.save(update_fields=['total_points'])
        return self.total_points
    
    def duplicate(self, new_title=None, creator=None):
        """Create a duplicate of this assessment"""
        new_assessment = Assessment(
            title=new_title or f"Copy of {self.title}",
            description=self.description,
            assessment_type=self.assessment_type,
            creator=creator or self.creator,
            subject_category=self.subject_category,
            difficulty_level=self.difficulty_level,
            time_limit=self.time_limit,
            max_attempts=self.max_attempts,
            passing_score=self.passing_score,
            randomize_questions=self.randomize_questions,
            randomize_choices=self.randomize_choices,
            show_correct_answers=self.show_correct_answers,
        )
        new_assessment.save()
        
        # Duplicate questions
        for question in self.questions.all():
            question.duplicate(new_assessment)
            
        new_assessment.calculate_total_points()
        return new_assessment

class Question(models.Model):
    """Enhanced question model with advanced features"""
    QUESTION_TYPES = (
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('identification', 'Identification'),
        ('enumeration', 'Enumeration'),
        ('essay', 'Essay'),
    )
    
    DIFFICULTY_LEVELS = (
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    )
    
    # Basic question information
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='questions', null=True, blank=True)
    question_bank = models.ForeignKey(QuestionBank, on_delete=models.CASCADE, related_name='questions', null=True, blank=True)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    question_text = models.TextField()
    
    # Enhanced question settings
    points = models.PositiveIntegerField(default=1)
    difficulty_level = models.CharField(max_length=10, choices=DIFFICULTY_LEVELS, default='medium')
    order = models.PositiveIntegerField(default=0)
    
    # Additional content
    explanation = models.TextField(
        blank=True,
        help_text="Explanation shown to students after answering (optional)"
    )
    hint = models.TextField(
        blank=True,
        help_text="Hint available to students (optional)"
    )
    image = models.ImageField(
        upload_to='questions/images/',
        blank=True,
        null=True,
        help_text="Optional image for the question"
    )
    
    # Question-specific settings
    expected_answers_count = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="For enumeration: number of expected answers"
    )
    is_case_sensitive = models.BooleanField(
        default=False,
        help_text="For text-based questions: whether answers are case sensitive"
    )
    allow_partial_credit = models.BooleanField(
        default=False,
        help_text="Allow partial credit for this question"
    )
    
    # Metadata
    usage_count = models.PositiveIntegerField(default=0)
    average_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    tags = models.CharField(max_length=300, blank=True, help_text="Comma-separated tags")
    
    # Source tracking
    imported_from_document = models.BooleanField(default=False)
    import_confidence = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Confidence score for imported questions (0-100)"
    )
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['question_type', 'difficulty_level']),
            models.Index(fields=['assessment', 'order']),
            models.Index(fields=['question_bank']),
        ]
    
    def __str__(self):
        assessment_part = f"{self.assessment.title} - " if self.assessment else ""
        bank_part = f"[{self.question_bank.name}] - " if self.question_bank else ""
        return f"{assessment_part}{bank_part}Q{self.order}: {self.question_text[:50]}..."
    
    def duplicate(self, target_assessment=None, target_bank=None):
        """Create a duplicate of this question"""
        new_question = Question(
            assessment=target_assessment or self.assessment,
            question_bank=target_bank or self.question_bank,
            question_type=self.question_type,
            question_text=self.question_text,
            points=self.points,
            difficulty_level=self.difficulty_level,
            explanation=self.explanation,
            hint=self.hint,
            expected_answers_count=self.expected_answers_count,
            is_case_sensitive=self.is_case_sensitive,
            allow_partial_credit=self.allow_partial_credit,
            tags=self.tags,
        )
        
        if target_assessment:
            # Set order for assessment
            max_order = target_assessment.questions.aggregate(
                models.Max('order')
            )['order__max'] or 0
            new_question.order = max_order + 1
        
        new_question.save()
        
        # Duplicate choices and correct answers
        for choice in self.choices.all():
            choice.duplicate(new_question)
        
        for answer in self.correct_answers.all():
            answer.duplicate(new_question)
            
        return new_question
    
    def update_statistics(self):
        """Update question statistics based on student responses"""
        if self.assessment:
            answers = StudentAnswer.objects.filter(question=self)
            if answers.exists():
                correct_answers = answers.filter(is_correct=True).count()
                self.average_score = (correct_answers / answers.count()) * 100
                self.usage_count = answers.count()
                self.save(update_fields=['average_score', 'usage_count'])
    
    def get_difficulty_color(self):
        """Get color code for difficulty level"""
        colors = {
            'easy': '#4caf50',
            'medium': '#ff9800', 
            'hard': '#f44336'
        }
        return colors.get(self.difficulty_level, '#9e9e9e')
    
    def validate_answer(self, student_answer):
        """Validate student answer and return score"""
        if self.question_type == 'multiple_choice':
            if hasattr(student_answer, 'selected_choice') and student_answer.selected_choice:
                return self.points if student_answer.selected_choice.is_correct else 0
        elif self.question_type == 'true_false':
            if hasattr(student_answer, 'selected_choice') and student_answer.selected_choice:
                return self.points if student_answer.selected_choice.is_correct else 0
        elif self.question_type in ['identification']:
            # Simple text matching for now - can be enhanced with fuzzy matching
            correct_answers = [answer.answer_text.lower() if not answer.is_case_sensitive 
                             else answer.answer_text for answer in self.correct_answers.all()]
            student_text = student_answer.text_answer
            if student_text:
                student_text = student_text.lower() if not self.is_case_sensitive else student_text
                if student_text in correct_answers:
                    return self.points
                # Partial credit logic can be added here
        elif self.question_type == 'enumeration':
            # Check enumeration answers
            correct_count = 0
            for answer in student_answer.enumeration_answers:
                if any(answer.lower() in correct.answer_text.lower() 
                       for correct in self.correct_answers.all()):
                    correct_count += 1
            
            if self.allow_partial_credit:
                return int((correct_count / max(self.expected_answers_count, 1)) * self.points)
            else:
                return self.points if correct_count >= self.expected_answers_count else 0
        
        return 0

class Choice(models.Model):
    """Enhanced answer choices for multiple choice and true/false questions"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    choice_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    # Enhanced features
    explanation = models.TextField(
        blank=True,
        help_text="Explanation for why this choice is correct/incorrect"
    )
    image = models.ImageField(
        upload_to='choices/images/',
        blank=True,
        null=True,
        help_text="Optional image for the choice"
    )
    
    # For partial credit
    partial_credit_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage of points to award for this choice"
    )
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.choice_text} ({'Correct' if self.is_correct else 'Incorrect'})"
    
    def duplicate(self, target_question):
        """Create a duplicate of this choice"""
        return Choice.objects.create(
            question=target_question,
            choice_text=self.choice_text,
            is_correct=self.is_correct,
            order=self.order,
            explanation=self.explanation,
            partial_credit_percentage=self.partial_credit_percentage,
        )

class CorrectAnswer(models.Model):
    """Enhanced correct answers for text-based questions"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='correct_answers')
    answer_text = models.TextField()
    is_case_sensitive = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    # Enhanced features
    is_exact_match = models.BooleanField(
        default=True,
        help_text="Require exact match or allow partial matching"
    )
    weight = models.DecimalField(
        max_digits=5, decimal_places=2, default=1.00,
        help_text="Weight of this answer for scoring"
    )
    keywords = models.CharField(
        max_length=500, blank=True,
        help_text="Keywords that must be present in student answer"
    )
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.question.question_text[:30]}... - {self.answer_text}"
    
    def duplicate(self, target_question):
        """Create a duplicate of this correct answer"""
        return CorrectAnswer.objects.create(
            question=target_question,
            answer_text=self.answer_text,
            is_case_sensitive=self.is_case_sensitive,
            order=self.order,
            is_exact_match=self.is_exact_match,
            weight=self.weight,
            keywords=self.keywords,
        )

class AssessmentGroup(models.Model):
    """Group assessments for organization"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assessment_groups')
    assessments = models.ManyToManyField(Assessment, blank=True, related_name='groups')
    
    # Settings
    is_public = models.BooleanField(default=False)
    color = models.CharField(max_length=7, default='#007bff', help_text="Hex color code")
    
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.name} ({self.assessments.count()} assessments)"

class AssessmentAnalytics(models.Model):
    """Store detailed analytics for assessments"""
    assessment = models.OneToOneField(Assessment, on_delete=models.CASCADE, related_name='analytics')
    
    # Performance metrics
    total_attempts = models.PositiveIntegerField(default=0)
    completed_attempts = models.PositiveIntegerField(default=0)
    average_completion_time = models.DurationField(null=True, blank=True)
    
    # Score distribution
    score_distribution = models.JSONField(default=dict, blank=True)
    question_analytics = models.JSONField(default=dict, blank=True)
    
    # Time-based metrics
    peak_usage_hours = models.JSONField(default=list, blank=True)
    daily_attempts = models.JSONField(default=dict, blank=True)
    
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Analytics for {self.assessment.title}"

class StudentAttempt(models.Model):
    """Enhanced student attempt tracking"""
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assessment_attempts')
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='attempts')
    
    # Timing
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_taken = models.DurationField(null=True, blank=True)
    time_remaining = models.DurationField(null=True, blank=True)
    
    # Scoring
    score = models.PositiveIntegerField(null=True, blank=True)
    max_score = models.PositiveIntegerField(null=True, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    weighted_score = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Status
    is_completed = models.BooleanField(default=False)
    is_passed = models.BooleanField(default=False)
    is_submitted = models.BooleanField(default=False)
    is_auto_submitted = models.BooleanField(default=False)
    
    # Attempt management
    attempt_number = models.PositiveIntegerField(default=1)
    current_question = models.PositiveIntegerField(default=1)
    
    # Security and tracking
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    browser_info = models.JSONField(default=dict, blank=True)
    
    # Proctoring data
    violation_flags = models.JSONField(default=list, blank=True)
    tab_switches = models.PositiveIntegerField(default=0)
    copy_paste_attempts = models.PositiveIntegerField(default=0)
    
    # Navigation tracking
    question_sequence = models.JSONField(default=list, blank=True)
    time_per_question = models.JSONField(default=dict, blank=True)
    
    class Meta:
        unique_together = ['student', 'assessment', 'attempt_number']
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['student', 'assessment']),
            models.Index(fields=['assessment', 'is_completed']),
        ]
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.assessment.title} (Attempt {self.attempt_number})"
    
    def calculate_score(self):
        """Calculate the final score for this attempt"""
        total_points = 0
        earned_points = 0
        
        for answer in self.answers.all():
            total_points += answer.question.points
            earned_points += answer.points_earned
        
        self.score = earned_points
        self.max_score = total_points
        self.percentage = (earned_points / max(total_points, 1)) * 100
        self.is_passed = self.percentage >= self.assessment.passing_score
        self.save(update_fields=['score', 'max_score', 'percentage', 'is_passed'])
        
        return self.percentage
    
    def get_time_taken(self):
        """Get formatted time taken"""
        if self.time_taken:
            total_seconds = int(self.time_taken.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        return "N/A"
    
    def add_violation(self, violation_type, details=None):
        """Add a security violation"""
        violation = {
            'type': violation_type,
            'timestamp': timezone.now().isoformat(),
            'details': details or {}
        }
        self.violation_flags.append(violation)
        self.save(update_fields=['violation_flags'])

class StudentAnswer(models.Model):
    """Enhanced student answer tracking"""
    attempt = models.ForeignKey(StudentAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    
    # Multiple choice and true/false answers
    selected_choice = models.ForeignKey(Choice, on_delete=models.CASCADE, null=True, blank=True)
    selected_choices = models.ManyToManyField(Choice, blank=True, related_name='multi_selections')
    
    # Text-based answers
    text_answer = models.TextField(blank=True, null=True)
    
    # Enumeration answers
    enumeration_answers = models.JSONField(default=list, blank=True)
    
    # Scoring
    is_correct = models.BooleanField(null=True, blank=True)
    points_earned = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_manually_graded = models.BooleanField(default=False)
    
    # Timing and behavior
    time_spent = models.DurationField(null=True, blank=True)
    answer_changes = models.PositiveIntegerField(default=0)
    is_flagged = models.BooleanField(default=False)
    flag_reason = models.CharField(max_length=200, blank=True)
    
    # File uploads (for essay questions)
    uploaded_file = models.FileField(
        upload_to='student_answers/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'txt'])]
    )
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['attempt', 'question']
        indexes = [
            models.Index(fields=['attempt', 'question']),
            models.Index(fields=['question', 'is_correct']),
        ]
    
    def __str__(self):
        return f"{self.attempt.student.get_full_name()} - {self.question.question_text[:30]}..."
    
    def auto_grade(self):
        """Automatically grade the answer based on question type"""
        if self.question.question_type in ['essay'] and not self.is_manually_graded:
            # Essay questions require manual grading
            return False
        
        self.points_earned = self.question.validate_answer(self)
        self.is_correct = self.points_earned > 0
        self.save(update_fields=['points_earned', 'is_correct'])
        return True
    
    def get_display_answer(self):
        """Get formatted answer for display"""
        if self.question.question_type == 'multiple_choice':
            return self.selected_choice.choice_text if self.selected_choice else "No answer"
        elif self.question.question_type == 'true_false':
            return self.selected_choice.choice_text if self.selected_choice else "No answer"
        elif self.question.question_type in ['identification', 'essay']:
            return self.text_answer or "No answer"
        elif self.question.question_type == 'enumeration':
            return ", ".join(self.enumeration_answers) if self.enumeration_answers else "No answer"
        
        return "No answer"
