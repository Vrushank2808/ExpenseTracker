from datetime import date, datetime, timedelta
from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, select

from .extensions import db
from .models import Category, Expense

main_bp = Blueprint("main", __name__)


def categories():
    return db.session.scalars(
        select(Category)
        .where(Category.user_id == current_user.id, Category.is_archived.is_(False))
        .order_by(Category.name)
    ).all()


def apply_expense_form(expense):
    title = request.form.get("title", "").strip()
    amount = request.form.get("amount", "").strip()
    category_id = request.form.get("category_id", type=int)
    expense_date = request.form.get("expense_date", "").strip()
    payment_method = request.form.get("payment_method", "").strip()
    if not title or not amount or not category_id or not expense_date or not payment_method:
        return "Please complete all required fields."
    try:
        expense.amount = Decimal(amount)
        expense.expense_date = datetime.strptime(expense_date, "%Y-%m-%d").date()
    except (ValueError, ArithmeticError):
        return "Enter a valid amount and date."
    if expense.amount <= 0:
        return "Amount must be greater than zero."
    category = db.session.scalar(
        select(Category).where(
            Category.id == category_id,
            Category.user_id == current_user.id,
            Category.is_archived.is_(False),
        )
    )
    if not category:
        return "Choose a valid category."
    expense.title = title
    expense.category_id = category_id
    expense.payment_method = payment_method
    expense.description = request.form.get("description", "").strip()
    return None


@main_bp.get("/")
def index():
    return redirect(url_for("main.dashboard" if current_user.is_authenticated else "auth.login"))


@main_bp.get("/dashboard")
@login_required
def dashboard():
    today = date.today()
    month_start = today.replace(day=1)
    month_expenses = db.session.scalars(
        select(Expense).where(Expense.user_id == current_user.id, Expense.expense_date >= month_start)
    ).all()
    total = sum((item.amount for item in month_expenses), Decimal("0"))
    recent = db.session.scalars(
        select(Expense).where(Expense.user_id == current_user.id).order_by(Expense.expense_date.desc()).limit(6)
    ).all()
    budget = Decimal("0")
    return render_template("dashboard.html", total=total, budget=budget, recent=recent, month_name=today.strftime("%B"))


@main_bp.route("/account", methods=["GET", "POST"])
@login_required
def account():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "name":
            name = request.form.get("name", "").strip()
            if not name:
                flash("Name cannot be empty.", "error")
            else:
                current_user.name = name
                db.session.commit()
                flash("Name updated successfully.", "success")
                return redirect(url_for("main.account"))
        elif action == "password":
            current_password = request.form.get("current_password", "")
            new_password = request.form.get("new_password", "")
            confirm_password = request.form.get("confirm_password", "")
            if not current_user.check_password(current_password):
                flash("Current password is incorrect.", "error")
            elif len(new_password) < 8:
                flash("New password must be at least 8 characters.", "error")
            elif new_password != confirm_password:
                flash("New passwords do not match.", "error")
            else:
                current_user.set_password(new_password)
                db.session.commit()
                flash("Password updated successfully.", "success")
                return redirect(url_for("main.account"))
    return render_template("account.html")


@main_bp.route("/expenses", methods=["GET", "POST"])
@login_required
def expenses():
    if request.method == "POST":
        expense = Expense(user_id=current_user.id)
        error = apply_expense_form(expense)
        if error:
            flash(error, "error")
        else:
            db.session.add(expense)
            db.session.commit()
            flash("Expense added successfully.", "success")
            return redirect(url_for("main.expenses"))
    query = select(Expense).where(Expense.user_id == current_user.id).order_by(Expense.expense_date.desc())
    search = request.args.get("search", "").strip()
    category_id = request.args.get("category_id", type=int)
    if search:
        query = query.where(Expense.title.ilike(f"%{search}%"))
    if category_id:
        query = query.where(Expense.category_id == category_id)
    expense_list = db.session.scalars(query).all()
    return render_template("expenses.html", expenses=expense_list, categories=categories(), filters=request.args)


@main_bp.route("/expenses/<int:expense_id>/edit", methods=["GET", "POST"])
@login_required
def edit_expense(expense_id):
    expense = db.session.scalar(select(Expense).where(Expense.id == expense_id, Expense.user_id == current_user.id))
    if not expense:
        return render_template("errors/404.html"), 404
    if request.method == "POST":
        error = apply_expense_form(expense)
        if error:
            flash(error, "error")
        else:
            db.session.commit()
            flash("Expense updated successfully.", "success")
            return redirect(url_for("main.expenses"))
    return render_template("expense_form.html", expense=expense, categories=categories())


@main_bp.post("/expenses/<int:expense_id>/delete")
@login_required
def delete_expense(expense_id):
    expense = db.session.scalar(select(Expense).where(Expense.id == expense_id, Expense.user_id == current_user.id))
    if expense:
        db.session.delete(expense)
        db.session.commit()
        flash("Expense deleted successfully.", "success")
    return redirect(url_for("main.expenses"))


@main_bp.route("/categories", methods=["GET", "POST"])
@login_required
def category_list():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        duplicate = db.session.scalar(
            select(Category).where(
                Category.user_id == current_user.id,
                Category.is_archived.is_(False),
                func.lower(Category.name) == name.lower(),
            )
        ) if name else True
        if name and not duplicate:
            db.session.add(Category(name=name, user_id=current_user.id))
            db.session.commit()
            flash("Category created successfully.", "success")
        else:
            flash("Enter a unique category name.", "error")
    return render_template("categories.html", categories=categories())


@main_bp.route("/categories/<int:category_id>/edit", methods=["GET", "POST"])
@login_required
def edit_category(category_id):
    category = db.session.scalar(
        select(Category).where(
            Category.id == category_id,
            Category.user_id == current_user.id,
            Category.is_archived.is_(False),
        )
    )
    if not category:
        return render_template("errors/404.html"), 404
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        duplicate = db.session.scalar(
            select(Category).where(
                Category.id != category.id,
                Category.user_id == current_user.id,
                Category.is_archived.is_(False),
                func.lower(Category.name) == name.lower(),
            )
        ) if name else True
        if not name or duplicate:
            flash("Enter a unique category name.", "error")
        else:
            category.name = name
            db.session.commit()
            flash("Category updated successfully.", "success")
            return redirect(url_for("main.category_list"))
    return render_template("category_form.html", category=category)


@main_bp.post("/categories/<int:category_id>/delete")
@login_required
def delete_category(category_id):
    category = db.session.scalar(
        select(Category).where(
            Category.id == category_id,
            Category.user_id == current_user.id,
            Category.is_archived.is_(False),
        )
    )
    if not category:
        return render_template("errors/404.html"), 404
    if category.expenses:
        category.is_archived = True
    else:
        db.session.delete(category)
    db.session.commit()
    flash("Category deleted successfully.", "success")
    return redirect(url_for("main.category_list"))


@main_bp.get("/reports")
@login_required
def reports():
    rows = db.session.execute(
        select(Category.name, func.sum(Expense.amount), func.count(Expense.id))
        .join(Expense, Expense.category_id == Category.id)
        .where(Expense.user_id == current_user.id, Category.user_id == current_user.id)
        .group_by(Category.name)
        .order_by(func.sum(Expense.amount).desc())
    ).all()
    return render_template("reports.html", rows=rows)
 