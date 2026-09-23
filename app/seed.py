from .extensions import db
from .models import Category, User

DEFAULT_CATEGORIES = ["Food", "Travel", "Shopping", "Bills", "Entertainment", "Healthcare", "Education", "Rent"]


def seed_defaults():
    for user in db.session.scalars(db.select(User)).all():
        existing = {
            category.name
            for category in db.session.scalars(
                db.select(Category).where(Category.user_id == user.id)
            ).all()
        }
        for name in DEFAULT_CATEGORIES:
            if name not in existing:
                db.session.add(Category(name=name, user_id=user.id))
    db.session.commit()
