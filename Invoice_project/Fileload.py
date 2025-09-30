import os, json
from typing import TypedDict, Dict, Any, List
import sqlite3
import os, json, time, sqlite3, warnings


INPUT_DIR     = "invoices"
DB_PATH       = "invoice.sqlite" 
PROCESSED_LOG = "processed.json"
POLL_SEC      = 5

os.makedirs(INPUT_DIR, exist_ok=True)

# read the invoice data from the file
def load_seen() -> set:
    if not os.path.exists(PROCESSED_LOG):
        return set()
    try:
        with open(PROCESSED_LOG, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()
    
# Previously read the data now into the load position
def save_seen(seen: set) -> None:
    with open(PROCESSED_LOG, "w", encoding="utf-8") as f:
        json.dump(sorted(list(seen)), f, ensure_ascii=False, indent=2)
        
seen = load_seen() 


# Create a Define a DB>> Sqlite3
def ensure_schema():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    # Create if missing
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS invoices (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          file_name TEXT,
          vendor TEXT,
          number TEXT,
          date TEXT,
          total REAL,
          currency TEXT,
          raw_json TEXT
        )
        """
    )
    # Add columns if table existed with an older schema
    cur.execute("PRAGMA table_info(invoices);")
    cols = {row[1] for row in cur.fetchall()}
    if "file_name" not in cols:
        cur.execute("ALTER TABLE invoices ADD COLUMN file_name TEXT;")
    if "raw_json" not in cols:
        cur.execute("ALTER TABLE invoices ADD COLUMN raw_json TEXT;")
    con.commit()
    con.close()

ensure_schema()
