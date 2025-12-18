import sqlite3
from pathlib import Path
DB_PATH = Path(__file__).resolve().parent / "app.db"
# Если кладёшь файл прямо в корень проекта, замени на:
# DB_PATH = Path(__file__).resolve().parent / "app.db"

def has_column(cur, table: str, col: str) -> bool:
    cur.execute(f"PRAGMA table_info({table});")
    return any(row[1] == col for row in cur.fetchall())

def add_column(cur, table: str, col_sql: str):
    cur.execute(f"ALTER TABLE {table} ADD COLUMN {col_sql};")

def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"DB not found: {DB_PATH}")

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    if not has_column(cur, "chat_threads", "close_low_confirmed"):
        add_column(cur, "chat_threads", "close_low_confirmed INTEGER NOT NULL DEFAULT 0")
        print("Added close_low_confirmed")
    else:
        print("close_low_confirmed already exists")

    if not has_column(cur, "chat_threads", "close_high_confirmed"):
        add_column(cur, "chat_threads", "close_high_confirmed INTEGER NOT NULL DEFAULT 0")
        print("Added close_high_confirmed")
    else:
        print("close_high_confirmed already exists")

    con.commit()
    con.close()
    print("OK")
if __name__ == "__main__":
    main()
