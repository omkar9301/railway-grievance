from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.orm import relationship
from datetime import datetime

db = SQLAlchemy()


# ================= USER MODEL =================
class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)   # Increased size for hashed passwords
    role = db.Column(db.String(50), nullable=False)

    # ✅ Department optional (Important fix)
    department = db.Column(db.String(100), nullable=True)

    # Relationships
    complaints = relationship(
        'Complaint',
        back_populates='user',
        foreign_keys='Complaint.user_id',
        cascade="all, delete"
    )

    assigned_complaints = relationship(
        'Complaint',
        back_populates='assigned_employee',
        foreign_keys='Complaint.assigned_employee_id'
    )


# ================= COMPLAINT MODEL =================
class Complaint(db.Model):
    __tablename__ = 'complaint'

    id = db.Column(db.Integer, primary_key=True)

    unique_id = db.Column(db.String, unique=True, nullable=False)

    department = db.Column(db.String, nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)

    pnr_no = db.Column(db.String, nullable=False)
    age = db.Column(db.Integer, nullable=False)

    additional_info = db.Column(db.Text, nullable=True)
    images = db.Column(db.String, nullable=True)

    status = db.Column(db.String(20), default='Unsolved')
    urgency = db.Column(db.Integer, default=0)

    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_employee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # Relationships
    user = relationship(
        'User',
        back_populates='complaints',
        foreign_keys=[user_id]
    )

    assigned_employee = relationship(
        'User',
        back_populates='assigned_complaints',
        foreign_keys=[assigned_employee_id]
    )

    feedbacks = db.relationship(
        'Feedback',
        back_populates='complaint',
        cascade="all, delete",
        lazy=True
    )


# ================= FEEDBACK MODEL =================
class Feedback(db.Model):
    __tablename__ = 'feedbacks'

    id = db.Column(db.Integer, primary_key=True)

    complaint_id = db.Column(db.Integer, db.ForeignKey('complaint.id'), nullable=False)

    feedback_text = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Pending')

    sentiment = db.Column(db.String(50), nullable=True)
    rating = db.Column(db.Integer, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    complaint = relationship('Complaint', back_populates='feedbacks')

    def __init__(self, complaint_id, feedback_text, sentiment, rating):
        self.complaint_id = complaint_id
        self.feedback_text = feedback_text
        self.sentiment = sentiment
        self.rating = rating
