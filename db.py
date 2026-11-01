import sqlite3
import os
from pathlib import Path

appdata = Path(os.getenv("APPDATA")) / "TaskNest"
appdata.mkdir(exist_ok=True)
db_name = str(appdata / "tasknest.db")


def get_conn():
    conn = sqlite3.connect(db_name)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS columns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                position INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                column_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                position INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (column_id) REFERENCES columns(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                color TEXT NOT NULL DEFAULT '#4FA8FF'
            );

            CREATE TABLE IF NOT EXISTS card_tags (
                card_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (card_id, tag_id),
                FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            );
        """)


def create_column(title, position=0):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO columns (title, position) VALUES(?, ?)",
            (title, position)
        )
        return cur.lastrowid


def get_all_columns():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM columns ORDER BY position, id"
        ).fetchall()
        return [dict(row) for row in rows]


def update_columns(column_id, title=None, position=None):
    with get_conn() as conn:
        if title is not None:
            conn.execute("UPDATE columns SET title = ? WHERE id = ?", (title, column_id))
        if position is not None:
            conn.execute("UPDATE columns SET position = ? WHERE id = ?", (position, column_id))


def delete_column(column_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM columns WHERE id = ?", (column_id,))


def create_card(column_id, title, description="", position=0):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO cards (column_id, title, description, position) VALUES (?, ?, ?, ?)",
            (column_id, title, description, position)
        )
        return cur.lastrowid


def get_cards_column(column_id):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM cards WHERE column_id = ? ORDER BY position, id",
            (column_id,)
        ).fetchall()
        return [dict(row) for row in rows]


def update_card(card_id, title=None, description=None, column_id=None, position=None):
    with get_conn() as conn:
        fields = []
        values = []

        if title is not None:
            fields.append("title = ?")
            values.append(title)
        if description is not None:
            fields.append("description = ?")
            values.append(description)
        if column_id is not None:
            fields.append("column_id = ?")
            values.append(column_id)
        if position is not None:
            fields.append("position = ?")
            values.append(position)
        if fields:
            values.append(card_id)
            conn.execute(f"UPDATE cards SET {', '.join(fields)} WHERE id = ?", values)


def delete_card(card_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM cards WHERE id = ?", (card_id,))


def create_tag(name, color="#4FA8FF"):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO tags (name, color) VALUES (?, ?)",
            (name, color)
        )
        return cur.lastrowid


def get_tags():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM tags ORDER BY id").fetchall()
        return [dict(row) for row in rows]


def delete_tag(tag_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM tags WHERE id = ?", (tag_id,))


def add_tag_to_card(card_id, tag_id):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO card_tags (card_id, tag_id) VALUES (?, ?)",
            (card_id, tag_id)
        )


def get_card_tags(card_id):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT tags.* FROM tags
            JOIN card_tags ON card_tags.tag_id = tags.id
            WHERE card_tags.card_id = ?
            ORDER BY tags.id
        """, (card_id,)).fetchall()
        return [dict(row) for row in rows]


def get_all_card_tags():
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT ct.card_id, t.id, t.name, t.color
            FROM card_tags ct
            JOIN tags t ON t.id = ct.tag_id
            ORDER BY t.id
        """).fetchall()
        result = {}
        for r in rows:
            result.setdefault(r["card_id"], []).append(
                {"id": r["id"], "name": r["name"], "color": r["color"]}
            )
        return result