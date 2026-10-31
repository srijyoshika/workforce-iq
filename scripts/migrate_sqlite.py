import sqlite3
import os

db_path = "workforce_iq_dev.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cols = [c[1] for c in cursor.execute("PRAGMA table_info(employees)").fetchall()]
    print("Existing employee columns:", cols)

    if "hashed_password" not in cols:
        cursor.execute("ALTER TABLE employees ADD COLUMN hashed_password VARCHAR(255)")
        print("Successfully added hashed_password column.")
    
    if "system_role" not in cols:
        cursor.execute("ALTER TABLE employees ADD COLUMN system_role VARCHAR(50) DEFAULT 'EMPLOYEE'")
        print("Successfully added system_role column.")

    conn.commit()
    conn.close()
    print("SQLite migration finished.")
else:
    print(f"{db_path} does not exist.")
