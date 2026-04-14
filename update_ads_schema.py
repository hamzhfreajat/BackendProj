import psycopg

def upgrade_schema():
    dsn = "postgresql://postgres:123456@localhost:5432/open"
    new_columns = {
        'expires_at': 'TIMESTAMP',
        'is_paused': 'BOOLEAN DEFAULT FALSE',
        'is_sold': 'BOOLEAN DEFAULT FALSE',
        'is_rejected': 'BOOLEAN DEFAULT FALSE',
        'rejected_reason': 'TEXT',
        'is_boosted': 'BOOLEAN DEFAULT FALSE',
        'boost_expiry': 'TIMESTAMP',
        'chats_count': 'INTEGER DEFAULT 0',
        'favorites_count': 'INTEGER DEFAULT 0'
    }
    
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cursor:
            # Get existing columns
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='ads'")
            existing_columns = [row[0] for row in cursor.fetchall()]
            
            for col_name, col_type in new_columns.items():
                if col_name not in existing_columns:
                    try:
                        print(f"Adding column {col_name}...")
                        cursor.execute(f"ALTER TABLE ads ADD COLUMN {col_name} {col_type}")
                        conn.commit()
                    except Exception as e:
                        print(f"Error adding {col_name}: {e}")
                        conn.rollback()
                else:
                    print(f"Column {col_name} already exists. Skipping.")
            
    print("Schema upgrade complete.")

if __name__ == "__main__":
    upgrade_schema()
