from datetime import date, datetime
from decimal import Decimal

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expenses = db.relationship("Expense", back_populates="user", cascade="all, delete-orphan")
    budgets = db.relationship("Budget", back_populates="user", cascade="all, delete-orphan")
    categories = db.relationship("Category", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(255), default="")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    is_archived = db.Column(db.Boolean, default=False, nullable=False)
    expenses = db.relationship("Expense", back_populates="category")
    user = db.relationship("User", back_populates="categories")


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    description = db.Column(db.Text, default="")
    expense_date = db.Column(db.Date, default=date.today, nullable=False)
    payment_method = db.Column(db.String(40), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    category = db.relationship("Category", back_populates="expenses")
    user = db.relationship("User", back_populates="expenses")


class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", back_populates="budgets")
    category = db.relationship("Category")

    __table_args__ = (db.UniqueConstraint("user_id", "month", "year", name="unique_user_budget_month"),)
