                                                                                                          TASK MANAGER


Live link: http://ec2-3-109-2-191.ap-south-1.compute.amazonaws.com/

1. Introduction
The Task Manager RBAC application is designed to enhance user experience and streamline interaction within organizational settings. Built using Python and Flask, it incorporates a robust Role-Based Access Control (RBAC) system to ensure secure user access. The application supports multiple user roles—Admin, Employee, and Support—each with specific functionalities tailored to their responsibilities.
Project Objectives
Develop an informative task management interface.
Implement a secure RBAC system for controlled access.
Utilize SQLite for persistent storage of user interactions and data.
Provide insightful data and analytics to drive improvements.
Deploy the application using modern web technologies for reliability and scalability.
2. Getting Started
Development Technologies
Programming Language: Python
Web Framework: Flask
Data Storage: SQLite (Flask-SQLAlchemy)
Front-End: HTML (Jinja2), CSS
Deployment: Docker, Gunicorn, AWS EC2
Data Visualization: Matplotlib
Project Features
The application offers the following key features:
Role-Based Access Control: Admin, Employee, and Support roles with distinct permissions.
Task Management: Creation, assignment, and tracking of tasks.
User Request Management: Handling requests for account modifications.
Data Storage: Utilizes SQLite for persistent storage with complex table relationships and 3NF normalization.
Real-Time Interaction: Provides an interactive web-based interface for real-time task management.


3. Database
the database structure using SQLAlchemy within a Flask application for a Task Manager with Role-Based Access Control (RBAC). Let's delve into the database structure in detail:
1. User Model

    Fields:
        id: Primary key, unique identifier for each user.
        username: Unique username for authentication.
        password: Password for authentication.
        role: Specifies the role of the user (Admin, Employee, Support).
        email: Unique email address for contact and authentication.

    Relationships:
        assigned_tasks: One-to-Many relationship with TaskAssignment model. Each user can have multiple assigned tasks.
        tasks_assigned: One-to-Many relationship with Task model. Each user can be the assigner of multiple tasks.
        extension_requests: One-to-Many relationship with ExtensionRequest model. Each user can initiate multiple extension requests.
Estimated Storage per User:
Integer fields: 4 bytes
String fields: 150 * 3 bytes (UTF-8 character size) = 450 bytes
Total per user: 4+450=4544 + 450 = 4544+450=454 bytes

2. Task Model

    Fields:
        id: Primary key, unique identifier for each task.
        title: Title of the task.
        description: Description of the task.
        category: Category of the task (e.g., Development, Marketing).
        start_date: Start date of the task.
        end_date: End date of the task.
        status: Current status of the task (e.g., Ongoing, Completed).
        assigned_by: Foreign key referencing the User who assigned the task.

    Relationships:
        assignments: One-to-Many relationship with TaskAssignment model. Each task can have multiple assignments.
        extension_requests: One-to-Many relationship with ExtensionRequest model. Each task can have multiple extension requests.

    Properties:
        no_of_days_given: Property calculating the duration of the task in days.
        actual_completion_date: Property returning the latest completion date among completed assignments.
        extra_time: Property calculating the total extra time granted through approved extension requests.
Estimated Storage per Task:
Integer fields: 4 + 4 = 8 bytes
String fields: 150 * 3 bytes = 450 bytes
Date fields: 4 + 4 = 8 bytes
Total per task: 8+450+8=4668 + 450 + 8 = 4668+450+8=466 bytes

3. TaskAssignment Model

    Fields:
        id: Primary key, unique identifier for each task assignment.
        user_id: Foreign key referencing the User assigned to the task.
        task_id: Foreign key referencing the Task being assigned.
        completed: Boolean indicating if the task assignment is completed.
        completion_date: Date when the task assignment was completed.

    Relationships:
        task: Many-to-One relationship with Task model. Each task assignment is linked to a specific task.
Estimated Storage per TaskAssignment:
Integer fields: 4 + 4 + 4 = 12 bytes
Boolean field: 1 byte
Date field: 4 bytes
Total per assignment: 12+1+4=1712 + 1 + 4 = 1712+1+4=17 bytes

4. ExtensionRequest Model

    Fields:
        id: Primary key, unique identifier for each extension request.
        task_id: Foreign key referencing the Task for which the extension is requested.
        user_id: Foreign key referencing the User requesting the extension.
        no_of_days: Number of days requested as an extension.
        reason: Justification for the extension request.
        status: Current status of the extension request (e.g., Pending, Approved).

    Relationships:
        task: Many-to-One relationship with Task model. Each extension request is linked to a specific task.
        requesting_user: Many-to-One relationship with User model. Each extension request is linked to a specific user.
Estimated Storage per ExtensionRequest:
Integer fields: 4 + 4 + 4 = 12 bytes
String fields: 50 * 3 bytes = 150 bytes
Total per request: 12+150=16212 + 150 = 16212+150=162 bytes

5. UserRequest Model (Assumed from the provided example)

    Fields:
        id: Primary key, unique identifier for each user request.
        username: Unique username for the user request.
        email: Unique email address for the user request.
        password: Password for the user request.
        role: Role assigned to the user request (default: 'employee').
        status: Current status of the user request (e.g., pending, approved)

    Purpose: The database structure supports a comprehensive Task Manager application with role-based access control, task management, extension requests, and user authentication.
    Usage: Utilizes SQLAlchemy for ORM operations, ensuring efficient database interactions within the Flask application.
    Design: Implements relationships such as one-to-many and many-to-one to establish connections between users, tasks, assignments, and extension requests.

This database schema provides a solid foundation for managing tasks, user roles, and interactions within an organization, facilitating effective task assignment, tracking, and management of user requests and extensions.
Sample estimation
The storage estimation for the database structure of the Task Manager application is based on assumptions of 1000 users, 500 tasks, 2000 task assignments, and 1000 extension requests. Each component contributes to the overall database size: users account for approximately 454 KB, tasks for about 233 KB, task assignments for around 34 KB, and extension requests for roughly 162 KB. These estimations consider the typical storage requirements for data fields such as usernames, passwords, task details, assignment statuses, and extension request details. It's essential to note that actual storage needs can vary due to factors like database indexes, overhead, and specific database management system settings. Regular monitoring and adjustment of storage capacity are recommended to optimize performance and ensure efficient data management as the application scales.

The database uses 3NF normalization form so that the data is stored and used efficiently without redundancy. 

4. User Features
Certainly! Here's a detailed explanation of the routes and their functionalities in the provided Flask application:
Authentication Blueprint (auth)
Login (/login):
Method: GET, POST
Function: Handles user login.
Process:
Renders the login form (LoginForm).
On form submission:
Validates user credentials (username and password hashed using check_password_hash).
Logs in the user using login_user from Flask-Login.
Redirects users based on their roles (admin, superuser, or employee).
Updates task statuses using update_task_status() upon successful login.
Sign Up (/Sign_up):
Method: GET, POST
Function: Allows new users to sign up with username, email, password, and role.
Process:
Renders the signup form (SignUpForm).
On form submission:
Hashes the password using generate_password_hash.
Creates a new UserRequest entity in the database with pending status.
Redirects to the login page upon successful signup.
Logout (/logout):
Method: GET
Function: Logs out the currently logged-in user.
Process:
Uses logout_user() from Flask-Login to log out the user.
Redirects to the home page (main.home).
View Requests (/admin/requests):
Method: GET
Function: Displays user registration requests for admin and superuser roles.
Process:
Fetches ExtensionRequest and UserRequest entities based on the user's role.
Renders respective templates (admin/user_request.html or superuser/superuser_requests.html).
Approve Request (/admin/approve/<int:request_id>):
Method: POST
Function: Allows admin to approve a user registration request.
Process:
Updates the status of the UserRequest entity to approved.
Creates a new User entity with the provided details (username, email, password, role).
Commits changes to the database.
Reject Request (/admin/reject/<int:request_id>):
Method: POST
Function: Allows admin to reject a user registration request.
Process:
Updates the status of the UserRequest entity to disapproved.
Commits changes to the database.
Delete Request (/delete_request/<int:request_id>):
Method: POST
Function: Deletes a user registration request.
Process:
Deletes the UserRequest entity from the database.
Flashes a success message upon deletion.
Superuser Employees (/superuser/employees):
Method: GET
Function: Lists all employees for superuser.
Process:
Fetches all User entities with role not equal to superuser.
Renders superuser/superuser_employees.html template with employee details.
Delete Employee (/superuser/delete_employee/<int:user_id>):
Method: POST
Function: Allows superuser to delete an employee.
Process:
Deletes the User entity with the specified user_id.
Flashes a success message upon deletion.
Reset Password (/superuser/reset_password/<int:user_id>):
Method: POST
Function: Allows superuser to reset an employee's password.
Process:
Updates the password of the User entity with the specified user_id using generate_password_hash.
Flashes success or error messages based on the outcome.
Change Email (/superuser/change_email/<int:user_id>):
Method: POST
Function: Allows superuser to change an employee's email address.
Process:
Updates the email of the User entity with the specified user_id.
Handles integrity errors (e.g., email already in use) using db.session.rollback() and flashes appropriate messages.
Main Blueprint (main)
Home (/):
Method: GET
Function: Renders the home page.
Admin Dashboard (/admin/dashboard):
Method: GET, POST
Function: Displays tasks filtered by employee, assigned by, category, and status for admin role.
Process:
Fetches tasks based on filter parameters (employee_id, assigned_by_id, category, status, sort_by, sort_order).
Updates task statuses using update_task_status().
Renders admin/dashboard.html template with tasks, employees, and admin-specific details.
Create Task (/admin/create_task):
Method: GET, POST
Function: Allows admin to create new tasks with details like title, description, category, start date, end date, and assign them to employees.
Process:
Renders the task creation form (admin/create_task.html).
On form submission:
Creates a new Task entity with provided details.
Creates TaskAssignment entities for assigned employers.
Sends email notifications to assigned employees and the admin.
Redirects to the admin dashboard upon successful task creation.
Edit Task (/admin/edit_task/<int:task_id>):
Method: GET, POST
Function: Allows admin to edit existing tasks including title, description, start date, end date, and status.
Process:
Fetches the Task entity with the specified task_id.
Renders the task editing form (admin/edit_task.html).
On form submission:
Updates the Task entity with modified details.
Commits changes to the database and redirects to the admin dashboard.
Employee Dashboard (/employee/dashboard):
Method: GET
Function: Lists tasks assigned to the logged-in employee.
Process:
Fetches TaskAssignment entities for the current user (employee role).
Renders employee/dashboard.html template with assigned tasks.
Complete Task (/employee/complete_task/<int:task_id>):
Method: POST
Function: Allows an employee to mark a task as completed.
Process:
Marks the TaskAssignment entity as completed for the specified task_id.
Checks if all task assignments are completed and updates task status accordingly (Completed, Late Submission).
Notifies the admin via email upon task completion.
Commits changes to the database and redirects to the employee dashboard.
Delete Task (/admin/delete_task/<int:task_id>):
Method: POST
Function: Allows admin to delete a task along with associated task assignments and extension requests.
Process:
Deletes Task, TaskAssignment, and ExtensionRequest entities related to the specified task_id.
Flashes a success message upon deletion and redirects to the admin dashboard.
Performance (/admin/performance):
Method: GET
Function: Provides a summary of task performance metrics (total tasks, completed tasks, ongoing tasks, overdue tasks, late submission tasks, success rate) for admin role.
Process:
Fetches task metrics based on filter parameters (employee_id).
Calculates success rate (% of completed tasks).
Renders admin/performance.html template with performance metrics.
Employees (/admin/employees):
Method: GET
Function: Lists all employees with task metrics (total tasks, completed tasks, ongoing tasks, overdue tasks, late submission tasks, success rate) for admin role.
Process:
Fetches User entities with role employee.
Calculates task metrics for each employee.
Renders admin/employees.html template with employee metrics.
Employee Performance (/admin/employee_performance/<int:employee_id>):
Method: GET
Function: Provides detailed performance metrics for a specific employee (total tasks, completed tasks, ongoing tasks, overdue tasks, late submission tasks, success rate).
Process:
Fetches User and TaskAssignment entities for the specified employee_id.
Calculates task metrics and success rate.
Renders admin/employee_performance.html template with employee performance details and a pie chart.
Request Extension (/request_extension/<int:task_id>):
Method: POST
Function: Allows an employee to request an extension for a task by specifying days and reason.
Process:
Creates an ExtensionRequest entity with Pending status.
Notifies the admin via email about the extension request.
Flashes a success message and redirects to the employee dashboard upon successful submission.
Approve Extension (/approve_extension/<int:request_id>):
Method: POST
Function: Allows admin to approve an extension request for a task.
Process:
Updates the ExtensionRequest entity status to Approved.
Extends the task deadline accordingly.
Notifies the employee via email about the approved extension.
Flashes a success message and redirects to the admin dashboard.
Reject Extension (/reject_extension/<int:request_id>):
Method: POST
Function: Allows admin to reject an extension request for a task.
Process:
Updates the ExtensionRequest entity status to Rejected.
Notifies the employee via email about the rejected extension.
Flashes a success message and redirects to the admin dashboard.


The Flask application provides comprehensive functionality for task management and user administration. Each role (admin, employee, superuser) has distinct capabilities tailored to their responsibilities within the organization. Admins oversee task creation, assignment, and management, while employees interact with assigned tasks and manage their profiles. Superusers handle user management tasks such as approving new registrations, managing employees, and resetting passwords. This breakdown ensures the application supports efficient task management and user administration workflows.

Based on the information provided and the routes discussed earlier, let's detail the security considerations implemented in your Flask application:
1. Data Encryption
Password Hashing

	Implementation:
    	Passwords are hashed using SHA-256 before storing them in the database.
    	This is achieved through Flask's generate_password_hash function from werkzeug.security, which securely hashes passwords.

Implementation Example:

	Login Route (/login):
    	When a user logs in, their provided password is hashed and compared with the hashed password stored in the database using check_password_hash.

python

from werkzeug.security import generate_password_hash, check_password_hash

# Example of hashing passwords
password = 'example_password'
hashed_password = generate_password_hash(password, method='sha256')

# Example of verifying hashed password
if check_password_hash(user.password_hash, provided_password):
	# Login successful
else:
	# Invalid credentials

2. User Authentication and Authorization
Flask-Login Integration

	Implementation:
    	User authentication is managed using Flask-Login, which provides a secure and flexible way to handle user sessions.
    	Different roles (admin, superuser, employee) are defined to control access to various routes and functionalities.

Authorization Example:

	Routes (/admin/*, /superuser/*, /employee/*):
    	Each route checks the user's role before granting access to sensitive operations such as task creation, user management, and task assignment.

python

from flask_login import current_user, login_required

# Example of restricting access based on user role
@app.route('/admin/create_task', methods=['GET', 'POST'])
@login_required
def create_task():
	if current_user.role != 'admin':
    	abort(403)  # Forbidden
	# Proceed with task creation logic
	...

3. Best Practices
CSRF Protection

	Implementation:
    	CSRF tokens are generated and verified for forms that perform sensitive operations like login, task creation, and user management.
    	This prevents CSRF attacks where unauthorized commands are transmitted from a user that the web application trusts.

Example:

	Login Route (/login), Create Task (/admin/create_task):
    	CSRF tokens are included in the forms rendered for these routes and validated upon form submission.

html

<!-- Example of CSRF token inclusion in a form -->
<form method="POST" action="/login">
	<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
	<!-- Other form fields -->
	<button type="submit">Login</button>
</form>

Admin Permissions for User Credentials

	Implementation:
    	Only the superuser role has the authority to create or manage admin level credentials.
    	Admin users can manage employee credentials but not superuser credentials, enforcing a hierarchical access control model.

Example:

	User Management Routes (/admin/*, /superuser/*):
    	Permission checks ensure that operations like creating new users or modifying existing credentials are restricted according to the user's role.

python

# Example of restricting admin credential creation
@app.route('/superuser/create_admin', methods=['GET', 'POST'])
@login_required
def create_admin():
	if current_user.role != 'superuser':
    	abort(403)  # Forbidden
	# Proceed with admin creation logic
	...

Summary

These security measures ensure that your Flask application follows best practices for data security, authentication, and authorization:

	Data Encryption: Passwords are securely hashed using SHA-256 before storage.
	User Authentication and Authorization: Flask-Login manages user sessions and restricts access based on defined roles (admin, superuser, employee).
	Best Practices: CSRF tokens are implemented to prevent CSRF attacks, and access to sensitive operations is restricted based on user roles (superuser for admin credentials, admin for employee credentials).

These measures collectively enhance the security of your application, safeguarding user data and preventing unauthorized access to sensitive functionalities.







