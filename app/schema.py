from sqlalchemy import inspect, text

from .extensions import db


def ensure_category_schema():
    inspector = inspect(db.engine)
    if "category" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("category")}
    has_global_unique_name = bool(inspector.get_unique_constraints("category"))
    if has_global_unique_name:
        _rebuild_category_table(columns)
        return

    with db.engine.begin() as connection:
        if "user_id" not in columns:
            connection.execute(text("ALTER TABLE category ADD COLUMN user_id INTEGER"))
        if "is_archived" not in columns:
            connection.execute(text("ALTER TABLE category ADD COLUMN is_archived BOOLEAN NOT NULL DEFAULT 0"))
        _assign_legacy_categories(connection)


def _assign_legacy_categories(connection):
    first_user = connection.execute(text("SELECT id FROM user ORDER BY id LIMIT 1")).scalar()
    if first_user is not None:
        connection.execute(
            text("UPDATE category SET user_id = :user_id WHERE user_id IS NULL"),
            {"user_id": first_user},
        )


def _rebuild_category_table(columns):
    with db.engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        connection.exec_driver_sql("PRAGMA legacy_alter_table=ON")
        connection.rollback()
        transaction = connection.begin()
        try:
            connection.execute(text("ALTER TABLE category RENAME TO category_legacy"))
            connection.execute(
                text(
                    """
                    CREATE TABLE category (
                        id INTEGER NOT NULL PRIMARY KEY,
                        name VARCHAR(80) NOT NULL,
                        description VARCHAR(255),
                        user_id INTEGER,
                        is_archived BOOLEAN NOT NULL DEFAULT 0,
                        FOREIGN KEY(user_id) REFERENCES user(id)
                    )
                    """
                )
            )
            user_column = "user_id" if "user_id" in columns else "NULL"
            archived_column = "is_archived" if "is_archived" in columns else "0"
            connection.execute(
                text(
                    f"INSERT INTO category (id, name, description, user_id, is_archived) "
                    f"SELECT id, name, description, {user_column}, {archived_column} FROM category_legacy"
                )
            )
            connection.execute(text("DROP TABLE category_legacy"))
            transaction.commit()
        except Exception:
            transaction.rollback()
            raise
        finally:
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")

    with db.engine.begin() as connection:
        _assign_legacy_categories(connection)
