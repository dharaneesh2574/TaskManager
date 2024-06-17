from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    
    assigned_tasks = db.relationship('TaskAssignment', backref='assigned_to', lazy=True)
    tasks_assigned = db.relationship('Task', backref='assigned_by_user', lazy=True)
    extension_requests = db.relationship('ExtensionRequest', back_populates='requesting_user', lazy=True, overlaps="user")

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Ongoing')
    assigned_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    assignments = db.relationship('TaskAssignment', back_populates='task', cascade="all, delete-orphan")
    extension_requests = db.relationship('ExtensionRequest', back_populates='task', cascade="all, delete-orphan")

class TaskAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    completion_date = db.Column(db.Date)

    task = db.relationship('Task', back_populates='assignments')

class ExtensionRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    new_end_date = db.Column(db.Date, nullable=False)
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
