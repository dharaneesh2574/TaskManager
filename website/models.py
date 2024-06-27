from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import timedelta

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    
    assigned_tasks = db.relationship('TaskAssignment', backref='assigned_to', lazy=True, cascade="all, delete-orphan")
    tasks_assigned = db.relationship('Task', backref=db.backref('assigned_by_user'), lazy=True)
    extension_requests = db.relationship('ExtensionRequest', back_populates='requesting_user', lazy=True, overlaps="user", cascade="all, delete-orphan")

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)  # New field for category
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Ongoing')
    assigned_by = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    
    assignments = db.relationship('TaskAssignment', back_populates='task', cascade="all, delete-orphan")
    extension_requests = db.relationship('ExtensionRequest', back_populates='task', cascade="all, delete-orphan")
    
    @property
    def no_of_days_given(self):
        return (self.end_date - self.start_date).days

    @property
    def actual_completion_date(self):
        completed_assignments = [assignment for assignment in self.assignments if assignment.completed]
        if completed_assignments:
            return max(assignment.completion_date for assignment in completed_assignments)
        return None

    @property
    def extra_time(self):
        approved_requests = [request for request in self.extension_requests if request.status == 'Approved']
        if approved_requests:
            return sum(request.no_of_days for request in approved_requests)
        return 0
    
    def get_final_end_date(self):
        """ Calculate the final end date considering any approved extension requests """
        final_end_date = self.end_date
        approved_requests = [request for request in self.extension_requests if request.status == 'Approved']
        for extension in approved_requests:
                final_end_date += timedelta(days=sum(request.no_of_days for request in approved_requests))
        return final_end_date


class TaskAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id', ondelete='CASCADE'), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    completion_date = db.Column(db.Date)

    task = db.relationship('Task', back_populates='assignments')

class ExtensionRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    no_of_days = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Pending')

    task = db.relationship('Task', back_populates='extension_requests')
    requesting_user = db.relationship('User', back_populates='extension_requests', overlaps="user")

class UserRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='employee')
    status = db.Column(db.String(50), nullable=False, default='pending')
