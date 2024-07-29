from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, Task, TaskAssignment, db, UserRequest, ExtensionRequest
from .forms import LoginForm, SignUpForm
from datetime import datetime, date, timedelta
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import func

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=True)
            update_task_status()
            if user.role == 'admin':
                return redirect(url_for('main.admin_dashboard'))
            elif user.role == 'superuser':
                return redirect(url_for('auth.view_requests'))
            else:
                return redirect(url_for('main.employee_dashboard'))
        flash('Invalid username or password')
    return render_template('login.html', form=form)


def update_task_status():
    current_date = datetime.now().date()  # Get the current date

    try:
        # Load all tasks with related extensions and assignments in a single query
        tasks = Task.query.options(
            joinedload(Task.extension_requests),
            joinedload(Task.assignments)
        ).all()

        for task in tasks:
            # Calculate the effective end date considering extra time
            approved_extensions = [ext.no_of_days for ext in task.extension_requests if ext.status == 'Approved']
            total_extra_days = sum(approved_extensions)
            effective_end_date = task.end_date + timedelta(days=total_extra_days)

            print(f"Task ID: {task.id}, End Date: {task.end_date}, Extra Days: {total_extra_days}, Effective End Date: {effective_end_date}, Current Date: {current_date}")

            if effective_end_date < current_date and task.status != 'Completed':
                task.status = 'Overdue'
            elif effective_end_date >= current_date and task.status == 'Overdue':
                task.status = 'Ongoing'

        # Update late submission tasks only if all assignments are completed
        overdue_tasks = Task.query.filter(Task.status == 'Overdue').all()
        for task in overdue_tasks:
            effective_end_date = task.end_date + timedelta(days=sum(ext.no_of_days for ext in task.extension_requests if ext.status == 'Approved'))
            all_completed = all(assignment.completed for assignment in task.assignments)
            if all_completed:
                any_late_submission = any(
                    assignment.completion_date and assignment.completion_date > effective_end_date
                    for assignment in task.assignments
                )
                if any_late_submission:
                    task.status = 'Late Submission'
                else:
                    task.status = 'Completed'

        # Commit all changes at once
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        flash('An error occurred while updating task statuses. Please try again.')
        print(f"Error: {e}")
        
@auth.route('/Sign_up', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        new_request = UserRequest(username=form.username.data, email=form.email.data, password=hashed_password, role=form.role.data)
        db.session.add(new_request)
        db.session.commit()
        return redirect(url_for('auth.login'))
    return render_template('Sign_up.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))

@auth.route('/admin/requests', methods=['GET'])
def view_requests():
    if current_user.role == 'admin': 
        extension_requests = ExtensionRequest.query.all()
        requests = UserRequest.query.filter_by(role='employee').all()
        return render_template('admin/user_request.html', extension_requests=extension_requests, requests=requests)
    elif current_user.role == 'superuser' :
        user_requests = UserRequest.query.all()
        return render_template('superuser/superuser_requests.html', user_requests=user_requests)
    else:
        return redirect(url_for('main.home'))

@auth.route('/admin/approve/<int:request_id>', methods=['POST'])
def approve_request(request_id):
    request = UserRequest.query.get_or_404(request_id)
    if request.status == 'pending':
        new_user = User(username=request.username, email=request.email, password=request.password, role=request.role)
        db.session.add(new_user)
        request.status = 'approved'
        db.session.commit()
    return redirect(url_for('auth.view_requests'))

@auth.route('/admin/reject/<int:request_id>', methods=['POST'])
def disapprove_request(request_id):
    request = UserRequest.query.get_or_404(request_id)
    if request.status == 'pending':
        request.status = 'disapproved'
        db.session.commit()
    return redirect(url_for('auth.view_requests'))

@auth.route('/delete_request/<int:request_id>', methods=['POST'])
@login_required
def delete_request(request_id):
    user_request = UserRequest.query.get_or_404(request_id)
    db.session.delete(user_request)
    db.session.commit()
    flash('Request deleted successfully.')
    return redirect(url_for('auth.view_requests'))

@auth.route('/superuser/employees', methods=['GET'])
@login_required
def superuser_employees():
    if current_user.role != 'superuser':
        return redirect(url_for('main.home'))

    employees = User.query.filter(User.role != 'superuser')
    return render_template('superuser/superuser_employees.html', employees=employees)

@auth.route('/superuser/delete_employee/<int:user_id>', methods=['POST'])
@login_required
def delete_employee(user_id):
    if current_user.role != 'superuser':
        return redirect(url_for('main.home'))

    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash('Employee deleted successfully')
    return redirect(url_for('auth.superuser_employees'))

@auth.route('/superuser/reset_password/<int:user_id>', methods=['POST'])
@login_required
def reset_password(user_id):
    if current_user.role != 'superuser':
        return redirect(url_for('main.home'))

    user = User.query.get(user_id)
    if not user:
        flash('User not found')
        return redirect(url_for('auth.superuser_employees'))

    new_password = request.form.get('new_password')
    repeat_password = request.form.get('repeat_password')

    if not new_password or not repeat_password:
        flash('Please provide both password fields')
        return redirect(url_for('auth.superuser_employees'))

    if new_password != repeat_password:
        flash('Passwords do not match')
        return redirect(url_for('auth.superuser_employees'))

    user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
    db.session.commit()
    flash('Password reset successfully')
    return redirect(url_for('auth.superuser_employees'))

@auth.route('/superuser/change_email/<int:user_id>', methods=['POST'])
@login_required
def change_email(user_id):
    if current_user.role != 'superuser':
        return redirect(url_for('main.home'))
    new_email = request.form.get('new_email')
    employee = User.query.get(user_id)
    if employee:
        employee.email = new_email
        try:
            db.session.commit()
            flash('Email updated successfully.', 'success')
        except IntegrityError:
            db.session.rollback()  # Roll back the session to the state before the commit
            flash('Email update failed. The email address is already in use.', 'danger')
    return redirect(url_for('auth.superuser_employees'))