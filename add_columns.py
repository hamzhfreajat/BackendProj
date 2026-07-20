from database import engine
from sqlalchemy import text

def run():
    with engine.connect() as conn:
        try:
            conn.execute(text('ALTER TABLE search_query_logs ADD COLUMN category_name VARCHAR(255);'))
            print('Added category_name')
        except Exception as e:
            print(e)
            
        try:
            conn.execute(text('ALTER TABLE search_query_logs ADD COLUMN extracted_tags VARCHAR(500);'))
            print('Added extracted_tags')
        except Exception as e:
            print(e)
            
        conn.commit()
if __name__ == '__main__':
    run()
