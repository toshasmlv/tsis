import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snake.db")

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS game_sessions (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id     INTEGER REFERENCES players(id),
                score         INTEGER NOT NULL,
                level_reached INTEGER NOT NULL,
                played_at     TIMESTAMP DEFAULT (datetime('now'))
            )
        """)
        conn.commit()

def get_or_create_player(username):
    with get_conn() as conn:
        cur = conn.execute("SELECT id FROM players WHERE username = ?", (username,))
        row = cur.fetchone()
        if row:
            return row[0]
        cur = conn.execute("INSERT INTO players (username) VALUES (?)", (username,))
        conn.commit()
        return cur.lastrowid

def save_session(username, score, level_reached):
    pid = get_or_create_player(username)
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO game_sessions (player_id, score, level_reached) VALUES (?, ?, ?)",
            (pid, score, level_reached)
        )
        conn.commit()

def get_top10():
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT p.username, gs.score, gs.level_reached,
                   strftime('%d.%m.%y', gs.played_at) as played_at
            FROM game_sessions gs
            JOIN players p ON p.id = gs.player_id
            ORDER BY gs.score DESC
            LIMIT 10
        """)
        return cur.fetchall()

def get_personal_best(username):
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT MAX(gs.score)
            FROM game_sessions gs
            JOIN players p ON p.id = gs.player_id
            WHERE p.username = ?
        """, (username,))
        row = cur.fetchone()
        return row[0] if row and row[0] else 0