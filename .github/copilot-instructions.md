<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# SPIST School Management System

This is a Django-based web application for Southern Philippines Institution of Science and Technology (SPIST) featuring separate authentication portals for students and teachers.

## Project Structure
- **Backend Framework**: Django 5.2.6
- **Database**: SQLite (for development)
- **Authentication**: Custom user model with separate student and teacher profiles
- **Frontend**: HTML templates with embedded CSS (functional design)

## Key Features
- Separate registration and login portals for students and teachers
- Custom user model extending AbstractUser
- Student profiles with course and year level information
- Teacher profiles with department and specialization details
- Role-based dashboard redirects
- Responsive design with clean UI

## Development Guidelines
- Focus on functionality over elaborate UI design
- Use Django best practices for security and authentication
- Maintain separate concerns for student and teacher functionality
- Ensure proper form validation and error handling

## Next Development Steps
- Add course management functionality
- Implement quiz/examination system
- Add grade management features
- Enhance dashboard with more interactive elements
