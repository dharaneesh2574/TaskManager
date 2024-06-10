from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, Task, TaskAssignment, db, UserRequest
from .forms import LoginForm, SignUpForm
from datetime import datetime

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=True)
            if user.role == 'admin':
                update_task_status()
                return redirect(url_for('main.admin_dashboard'))
            else:
                update_task_status()
                return redirect(url_for('main.employee_dashboard'))
        flash('Invalid username or password')
    return render_template('login.html', form=form)

def update_task_status():
    current_date = datetime.now().date()

    
    overdue_tasks = Task.query.filter(Task.end_date < current_date, Task.status != 'Completed').all()
    for task in overdue_tasks:
        task.status = 'Overdue'
        db.session.commit()

    late_submission_tasks = Task.query.filter(Task.status == 'Overdue').all()
    for task in late_submission_tasks:
        task_assignments = TaskAssignment.query.filter_by(task_id=task.id, completed=True).all()
        for assignment in task_assignments:
            if assignment.completion_date > task.end_date:
                task.status = 'Late Submission'
                db.session.commit()
                break

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
    requests = UserRequest.query.filter_by(status='pending').all()
    return render_template('admin/user_request.html', requests=requests)

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
def reject_request(request_id):
    request = UserRequest.query.get_or_404(request_id)
    if request.status == 'pending':
        request.status = 'rejected'
        db.session.commit()
    return redirect(url_for('auth.view_requests'))