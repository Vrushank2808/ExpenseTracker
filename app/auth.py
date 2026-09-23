from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy import select

from .extensions import db
from .models import Category, User
from .seed import DEFAULT_CATEGORIES

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 8:
            flash("Use a name, a valid email, and a password with at least 8 characters.", "error")
        elif db.session.scalar(select(User).where(User.email == email)):
            flash("An account with that email already exists.", "error")
        else:
            user = User(name=name, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.flush()
            db.session.add_all(
                [Category(name=category_name, user_id=user.id) for category_name in DEFAULT_CATEGORIES]
            )
            db.session.commit()
            login_user(user)
            return redirect(url_for("main.dashboard"))
    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = db.session.scalar(select(User).where(User.email == email))
        if not user or not user.check_password(request.form.get("password", "")):
            flash("Email or password is incorrect.", "error")
        else:
            login_user(user)
            return redirect(url_for("main.dashboard"))
    return render_template("auth/login.html")


@auth_bp.post("/logout")
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))
