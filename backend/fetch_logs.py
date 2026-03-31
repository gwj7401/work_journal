import mysql.connector
import json

def fetch_march_logs():
    conn = mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="Szs123456@",
        database="work_journal_db"
    )
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT entry_date, content, tags
        FROM journal_entries
        WHERE entry_date >= '2026-03-01' AND entry_date <= '2026-03-31'
        ORDER BY entry_date ASC
    """)
    rows = cursor.fetchall()
    
    with open('f:/work-journal/docs/march_logs.json', 'w', encoding='utf-8') as f:
        # Convert dates to string for JSON serialization
        for row in rows:
            row['entry_date'] = str(row['entry_date'])
        json.dump(rows, f, ensure_ascii=False, indent=2)

    cursor.close()
    conn.close()

if __name__ == "__main__":
    fetch_march_logs()
