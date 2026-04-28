from database import SessionLocal
from sqlalchemy import text
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

db = SessionLocal()
try:
    with open('db_stats.txt', 'w', encoding='utf-8') as f:
        count = db.execute(text("SELECT COUNT(*) FROM ai_training_logs")).scalar()
        success_count = db.execute(text("SELECT COUNT(*) FROM ai_training_logs WHERE status='success'")).scalar()
        f.write(f"Total logs: {count}\n")
        f.write(f"Successful logs: {success_count}\n")
        
        results = db.execute(text("SELECT status, post_text, ai_output FROM ai_training_logs LIMIT 3")).fetchall()
        f.write("\nSample:\n")
        for r in results:
            f.write(f"Status: {r[0]}\n")
            f.write(f"Text: {r[1][:200] if r[1] else ''}\n")
            f.write(f"Out: {r[2]}\n")
            f.write("-----\n")
except Exception as e:
    print(e)
