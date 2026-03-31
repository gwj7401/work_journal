import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine
from sqlalchemy import text

def add_column():
    queries = [
        "ALTER TABLE monthly_summaries ADD COLUMN is_final BOOLEAN DEFAULT 0;",
        "ALTER TABLE quarterly_summaries ADD COLUMN is_final BOOLEAN DEFAULT 0;",
        "ALTER TABLE annual_summaries ADD COLUMN is_final BOOLEAN DEFAULT 0;"
    ]
    with engine.connect() as conn:
        for q in queries:
            try:
                conn.execute(text(q))
                print(f"Executed: {q}")
            except Exception as e:
                print(f"Error on {q}: {e}")
        conn.commit()
    print("Migration finished.")

if __name__ == "__main__":
    add_column()
