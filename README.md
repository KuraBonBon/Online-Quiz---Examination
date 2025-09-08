# SPIST School Management System

A Django-based web application for Southern Philippines Institution of Science and Technology (SPIST) with separate authentication portals for students and teachers.

## Features

### Authentication System
- **Dual Portal Design**: Separate login/registration for students and teachers
- **Custom User Model**: Extended Django user model with role-based profiles
- **Email-based Login**: Users authenticate using email addresses
- **Role-based Redirects**: Automatic dashboard routing based on user type

### Student Portal
- Student registration with course and year level information
- Student-specific dashboard with personal information
- Student ID tracking and course enrollment details

### Teacher Portal
- Teacher registration with department and specialization details
- Teacher-specific dashboard with professional information
- Employee ID tracking and departmental assignments

## Project Structure

```
spist_school/
├── manage.py
├── spist_school/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── accounts/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── forms.py
    ├── models.py
    ├── urls.py
    ├── views.py
    ├── migrations/
    └── templates/
        └── accounts/
            ├── base.html
            ├── home.html
            ├── login.html
            ├── student_register.html
            ├── teacher_register.html
            ├── student_dashboard.html
            └── teacher_dashboard.html
```

## Installation and Setup

1. **Clone the repository**:
   ```bash
   cd "Online Quiz & Examination"
   ```

2. **Install dependencies**:
   ```bash
   pip install django
   ```

3. **Run migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Create a superuser** (optional):
   ```bash
   python manage.py createsuperuser
   ```

5. **Start the development server**:
   ```bash
   python manage.py runserver
   ```

6. **Access the application**:
   - Home page: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/

7. **Create sample users** (optional):
   ```bash
   python manage.py create_sample_users
   ```

## Sample Login Credentials

After running the `create_sample_users` command, you can use these test accounts:

### Student Account
- **Email**: student@spist.edu
- **Password**: password123
- **Profile**: John Doe, Computer Science, 3rd Year

### Teacher Account
- **Email**: teacher@spist.edu  
- **Password**: password123
- **Profile**: Jane Smith, Computer Science Department

### Admin Account
- **Email**: admin@spist.edu
- **Password**: admin123
- **Access**: Full admin panel access

## Usage

### For Students
1. Visit the home page and select "Student Portal"
2. Register using the student registration form
3. Login with your email and password
4. Access your student dashboard

### For Teachers
1. Visit the home page and select "Teacher Portal"
2. Register using the teacher registration form
3. Login with your email and password
4. Access your teacher dashboard

## Models

### User Model
- Extended AbstractUser with additional fields:
  - `user_type`: Student or Teacher
  - `email`: Unique email field (used for login)
  - `phone_number`: Optional contact number
  - `is_verified`: Account verification status

### StudentProfile Model
- One-to-one relationship with User
- Fields: student_id, course, year_level, date_enrolled

### TeacherProfile Model
- One-to-one relationship with User
- Fields: employee_id, department, specialization, hire_date

## Technology Stack

- **Backend**: Django 5.2.6
- **Database**: SQLite (development)
- **Frontend**: HTML templates with embedded CSS
- **Authentication**: Django's built-in authentication system with custom user model

## Future Development

The system is designed to be easily extensible for additional features such as:
- Course management
- Quiz and examination system
- Grade tracking
- Assignment submissions
- Real-time notifications
- File sharing capabilities

## Contributing

This project serves as a foundation for a comprehensive school management system. Focus areas for expansion include:
- Enhanced UI/UX design
- API development for mobile applications
- Integration with external systems
- Advanced reporting and analytics

## License

This project is developed for educational purposes as part of the SPIST school management system.
