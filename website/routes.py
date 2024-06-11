from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from .models import Task, TaskAssignment, User, db, ExtensionRequest
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from .forms import ProfileForm
from .email_utils import send_email
import datetime
import matplotlib.pyplot as plt
import os
import matplotlib
matplotlib.use('Agg')

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return render_template('home.html')


@main.route('/admin/dashboard', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('main.home'))

    employee_id = request.args.get('employee_id', type=int)
    sort_by = request.args.get('sort_by', 'start_date')
    sort_order = request.args.get('sort_order', 'asc')

    tasks_query = Task.query
    extension_requests_query = ExtensionRequest.query

    if employee_id:
        tasks_query = tasks_query.join(TaskAssignment).filter(TaskAssignment.user_id == employee_id)
        extension_requests_query = extension_requests_query.filter_by(user_id=employee_id)

    if sort_by and sort_order:
        if sort_order == 'asc':
            if sort_by == 'start_date':
                tasks_query = tasks_query.order_by(Task.start_date.asc())
                extension_requests_query = extension_requests_query.order_by(ExtensionRequest.new_end_date.asc())
            elif sort_by == 'end_date':
                tasks_query = tasks_query.order_by(Task.end_date.asc())
                extension_requests_query = extension_requests_query.order_by(ExtensionRequest.new_end_date.asc())
        else:
            if sort_by == 'start_date':
                tasks_query = tasks_query.order_by(Task.start_date.desc())
                extension_requests_query = extension_requests_query.order_by(ExtensionRequest.new_end_date.desc())
            elif sort_by == 'end_date':
                tasks_query = tasks_query.order_by(Task.end_date.desc())
                extension_requests_query = extension_requests_query.order_by(ExtensionRequest.new_end_date.desc())

    tasks = tasks_query.all()
    employees = User.query.filter_by(role='employee').all()
    extension_requests = extension_requests_query.all()

    return render_template('admin/dashboard.html', tasks=tasks, employees=employees, extension_requests=extension_requests)

@main.route('/admin/create_task', methods=['GET', 'POST'])
@login_required
def create_task():
    if current_user.role != 'admin':
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        assigned_to_ids = request.form.getlist('assigned_to')

        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()

        new_task = Task(
            title=title,
            description=description,
            start_date=start_date,
            end_date=end_date,
            status='Ongoing',
            assigned_by=current_user.id
        )
        db.session.add(new_task)
        db.session.commit()

        # Handle task assignments and send email to employees
        for user_id in assigned_to_ids:
            task_assignment = TaskAssignment(user_id=user_id, task_id=new_task.id)
            db.session.add(task_assignment)
            
            # Fetch employee email and send email notification
            employee = User.query.get(user_id)
            subject = "New Task Assigned"
            body = f"Dear {employee.username},\n\nYou have been assigned a new task:\n\nTitle: {title}\nDescription: {description}\nStart Date: {start_date}\nEnd Date: {end_date}\n\nBest regards,\nYour Admin"
            send_email(employee.email, subject, body)

        # Send email notification to the admin who created the task
        admin_email = current_user.email
        subject = "Task Created"
        body = f"Hello {current_user.username},\n\nYou have successfully created a new task: {title}\nDescription: {description}\nStart Date: {start_date}\nEnd Date: {end_date}\n\nBest regards,\nTask Management System"
        send_email(admin_email, subject, body)
        
        db.session.commit()
        return redirect(url_for('main.admin_dashboard'))

    employees = User.query.filter_by(role='employee').all()
    return render_template('admin/create_task.html', employees=employees)


@main.route('/admin/edit_task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    if current_user.role != 'admin':
        return redirect(url_for('main.home'))

    task = Task.query.get_or_404(task_id)

    if request.method == 'POST':
        task.title = request.form.get('title')
        task.description = request.form.get('description')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        task.status = request.form.get('status')

        task.start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        task.end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        db.session.commit()
        return redirect(url_for('main.admin_dashboard'))

    employees = User.query.filter_by(role='employee').all()
    return render_template('admin/edit_task.html', task=task, employees=employees)

@main.route('/employee/dashboard')
@login_required
def employee_dashboard():
    if current_user.role != 'employee':
        return redirect(url_for('main.home'))

    tasks = TaskAssignment.query.filter_by(user_id=current_user.id).all()
    return render_template('employee/dashboard.html', tasks=tasks)

@main.route('/employee/complete_task/<int:task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    if current_user.role != 'employee':
        return redirect(url_for('main.home'))

    task_assignment = TaskAssignment.query.filter_by(user_id=current_user.id, task_id=task_id).first_or_404()
    task_assignment.completed = True
    task_assignment.completion_date = datetime.datetime.now()

    task = Task.query.get_or_404(task_id)
    end_date = datetime.datetime.combine(task.end_date, datetime.datetime.min.time())
    task.status = 'Completed'

    if end_date < datetime.datetime.now():
        task.status = 'Late Submission'

    db.session.commit()
    #admin = User.query.get(task.assigned_by_user)
    email_subject = "Task Completed"
    email_body = f"Hello {task.assigned_by_user.username},\n\nThe task '{task.title}' assigned to {current_user.username} has been marked as completed.\n\nBest regards,\nTask Management System"

    if end_date < datetime.datetime.now():
        task.status = 'Late Submission'
        email_subject = "Task Completed Late"
        email_body = f"Hello {task.assigned_by_user.username},\n\nThe task '{task.title}' assigned to {current_user.username} has been completed but was submitted late.\n\nBest regards,\nTask Management System"

    
    if task.assigned_by_user:
        send_email(task.assigned_by_user.email, email_subject, email_body)

    return redirect(url_for('main.employee_dashboard'))

@main.route('/admin/delete_task/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    if current_user.role != 'admin':
        return redirect(url_for('main.home'))

    task = Task.query.get_or_404(task_id)
    
    # Delete associated task assignments and extension requests
    TaskAssignment.query.filter_by(task_id=task_id).delete()
    ExtensionRequest.query.filter_by(task_id=task_id).delete()

    db.session.delete(task)
    db.session.commit()
    
    flash('Task and associated records deleted successfully.')
    return redirect(url_for('main.admin_dashboard'))


@main.route('/admin/performance')
@login_required
def performance():
    if current_user.role != 'admin':
        return redirect(url_for('main.home'))

    total_tasks = Task.query.count()
    completed_tasks = Task.query.filter_by(status='Completed').count()
    ongoing_tasks = Task.query.filter_by(status='Ongoing').count()
    overdue_tasks = Task.query.filter_by(status='Overdue').count()
    late_submission_tasks = Task.query.filter(Task.assignments.any(TaskAssignment.completed == False)).filter(Task.end_date < db.func.current_date()).count()

    success_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0

    return render_template('admin/performance.html',
                           total_tasks=total_tasks,
                           completed_tasks=completed_tasks,
                           ongoing_tasks=ongoing_tasks,
                           overdue_tasks=overdue_tasks,
                           late_submission_tasks=late_submission_tasks,
                           success_rate=success_rate)

@main.route('/admin/employees')
@login_required
def employees():
    employees = User.query.filter_by(role='employee').all()

    employee_metrics = []
    for employee in employees:
        total_tasks = len(employee.assigned_tasks)
        completed_tasks = sum(1 for task in employee.assigned_tasks if task.task.status == 'Completed')
        ongoing_tasks = sum(1 for task in employee.assigned_tasks if task.task.status == 'Ongoing')
        overdue_tasks = sum(1 for task in employee.assigned_tasks if task.task.status == 'Overdue')
        late_submission_tasks = sum(1 for task in employee.assigned_tasks if task.task.status == 'Late Submission')
        success_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0

        employee_metrics.append({
            'employee': employee,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'ongoing_tasks': ongoing_tasks,
            'overdue_tasks': overdue_tasks,
            'late_submission_tasks': late_submission_tasks,
            'success_rate': success_rate
        })

    return render_template('admin/employees.html', employee_metrics=employee_metrics)


@main.route('/admin/employee_performance/<int:employee_id>')
@login_required
def employee_performance(employee_id):
    employee = User.query.get_or_404(employee_id)
    
    task_assignments = TaskAssignment.query.filter_by(user_id=employee_id).all()
    total_tasks = len(task_assignments)
    completed_tasks = sum(1 for assignment in task_assignments if assignment.completed)
    ongoing_tasks = total_tasks - completed_tasks
    overdue_tasks = sum(1 for assignment in task_assignments if assignment.task.end_date < datetime.date.today() and not assignment.completed)
    late_submission_tasks = sum(1 for assignment in task_assignments if assignment.completed and assignment.completion_date and assignment.completion_date > assignment.task.end_date)
    success_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0

    # Prepare data for the pie chart
    labels = ['Completed', 'Ongoing', 'Overdue', 'Late Submission']
    sizes = [completed_tasks, ongoing_tasks, overdue_tasks, late_submission_tasks]
    colors = ['#4CAF50', '#2196F3', '#FF5722', '#FFC107']

    # Check if data arrays are valid
    if sum(sizes) == 0:
        sizes = [1]  # Prevent empty pie chart error
        labels = ['No Tasks']
        colors = ['#D3D3D3']
        explode = [0]  # No explosion needed for a single slice
    else:
        explode = [0.1] + [0] * (len(sizes) - 1)  # Explode the first slice (i.e. 'Completed')

    fig, ax = plt.subplots()
    ax.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
           shadow=True, startangle=140)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    # Ensure the static directory exists
    static_dir = os.path.join('website', 'static')
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)

    # Save the pie chart
    pie_chart_filename = f'pie_chart_{employee_id}.png'
    pie_chart_path = os.path.join(static_dir, pie_chart_filename)
    plt.savefig(pie_chart_path)
    plt.close(fig)  # Close the figure to free up memory

    return render_template('admin/employee_performance.html', employee=employee,
                           total_tasks=total_tasks, completed_tasks=completed_tasks,
                           ongoing_tasks=ongoing_tasks, overdue_tasks=overdue_tasks,
                           late_submission_tasks=late_submission_tasks,
                           success_rate=success_rate, pie_chart_filename=pie_chart_filename,
                           assigned_tasks=task_assignments)



def generate_pie_chart(total_tasks, completed_tasks, ongoing_tasks, overdue_tasks, late_submission_tasks, employee_id):
    labels = ['Completed', 'Ongoing', 'Overdue', 'Late Submission']
    sizes = [completed_tasks, ongoing_tasks, overdue_tasks, late_submission_tasks]
    colors = ['#4CAF50', '#FFC107', '#F44336', '#9E9E9E']
    explode = (0.1, 0, 0, 0)

    fig, ax = plt.subplots()
    ax.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
           shadow=True, startangle=140)
    ax.axis('equal')

    static_dir = os.path.join('website', 'static')
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)

    chart_path = os.path.join(static_dir, f'pie_chart_{employee_id}.png')
    plt.savefig(chart_path)
    plt.close()
    return chart_path

@main.route('/request_extension/<int:task_id>', methods=['POST'])
@login_required
def request_extension(task_id):
    new_end_date_str = request.form.get('new_end_date')
    reason = request.form.get('reason')

    try:
        new_end_date = datetime.datetime.strptime(new_end_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format. Please use YYYY-MM-DD.')
        return redirect(url_for('dashboard'))

    extension_request = ExtensionRequest(
        task_id=task_id,
        user_id=current_user.id,
        new_end_date=new_end_date,
        reason=reason,
        status='Pending'
    )

    db.session.add(extension_request)
    db.session.commit()

    # Get the task details
    task = Task.query.get_or_404(task_id)
    admin_user = User.query.get(task.assigned_by)
    
    if admin_user:
        email_subject = "Extension Request Submitted"
        email_body = f"Hello {admin_user.username},\n\nThe employee {current_user.username} has requested an extension for the task '{task.title}'.\n\nNew End Date: {new_end_date_str}\nReason: {reason}\n\nBest regards,\nTask Management System"
        send_email(admin_user.email, email_subject, email_body)

    flash('Extension request submitted successfully.')
    return redirect(url_for('main.employee_dashboard'))

@main.route('/approve_extension/<int:request_id>', methods=['POST'])
@login_required
def approve_extension(request_id):
    if current_user.role != 'admin':
        return redirect(url_for('main.home'))
    extension_request = ExtensionRequest.query.get_or_404(request_id)
    extension_request.status = 'Approved'
    task = Task.query.get(extension_request.task_id)
    task.end_date = extension_request.new_end_date
    db.session.commit()
    return redirect(url_for('main.admin_dashboard'))

@main.route('/disapprove_extension/<int:request_id>', methods=['POST'])
@login_required
def disapprove_extension(request_id):
    if current_user.role != 'admin':
        return redirect(url_for('main.home'))
    extension_request = ExtensionRequest.query.get_or_404(request_id)
    extension_request.status = 'Disapproved'
    db.session.commit()
    return redirect(url_for('main.admin_dashboard'))

@main.route('/admin/delete_extension_request/<int:request_id>', methods=['POST'])
@login_required
def delete_extension_request(request_id):
    if current_user.role != 'admin':
        return redirect(url_for('main.home'))

    extension_request = ExtensionRequest.query.get_or_404(request_id)
    db.session.delete(extension_request)
    db.session.commit()
    
    flash('Extension request deleted successfully.')
    return redirect(url_for('main.admin_dashboard'))

@main.route('/delete_employee/<int:employee_id>', methods=['POST'])
@login_required
def delete_employee(employee_id):
    employee = User.query.get_or_404(employee_id)
    if employee.role != 'employee':
        flash('Cannot delete this user.', 'danger')
        return redirect(url_for('main.employees'))
    
    db.session.delete(employee)
    db.session.commit()
    flash(f'Employee {employee.username} has been deleted.', 'success')
    return redirect(url_for('main.employees'))

@main.route('/employee/profile', methods=['GET', 'POST'])
@login_required
def my_profile():
    if current_user.role != 'employee':
        return redirect(url_for('main.home'))

    form = ProfileForm()

    if form.validate_on_submit():
        current_user.email = form.email.data
        if form.password.data:
            current_user.password = generate_password_hash(form.password.data)
        
        if form.profile_photo.data:
            filename = secure_filename(form.profile_photo.data.filename)
            filepath = os.path.join('static/profile_photos', filename)
            form.profile_photo.data.save(filepath)
            current_user.profile_photo = filepath

        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('main.my_profile'))

    form.email.data = current_user.email
    return render_template('employee/profile.html', form=form)
