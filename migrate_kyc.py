from database import engine
from sqlalchemy import text

statements = [
    "ALTER TABLE users ADD COLUMN full_name VARCHAR(100);",
    "ALTER TABLE users ADD COLUMN national_id VARCHAR(20) UNIQUE;",
    "ALTER TABLE users ADD COLUMN date_of_birth VARCHAR(20);",
    "ALTER TABLE users ADD COLUMN id_expiry_date VARCHAR(20);",
    "ALTER TABLE users ADD COLUMN identity_document_url TEXT;",
    "ALTER TABLE users ADD COLUMN liveness_passed BOOLEAN DEFAULT FALSE;",
    "ALTER TABLE users ADD COLUMN face_similarity_score DECIMAL(5, 2);",
    "ALTER TABLE users ADD COLUMN verification_status VARCHAR(20) DEFAULT 'pending';"
]

with engine.connect() as conn:
    for stmt in statements:
        try:
            conn.execute(text(stmt))
            conn.commit()
            print(f"Executed: {stmt}")
        except Exception as e:
            print(f"Skipped/Failed for {stmt}: {e}")
            conn.rollback()

print("Done")
