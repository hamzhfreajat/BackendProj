import re

filepath = 'D:/open/classifieds-app/backend/main.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

if "upgrade-db" in content:
    print("Already added")
else:
    endpoint_code = """
@app.get("/api/admin/upgrade-db")
def upgrade_db(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    from sqlalchemy import text
    commands = [
        "ALTER TABLE ads ADD COLUMN IF NOT EXISTS duplicate_status VARCHAR(50);",
        "ALTER TABLE ads ADD COLUMN IF NOT EXISTS highest_duplicate_score INTEGER;",
        "ALTER TABLE ads ADD COLUMN IF NOT EXISTS market_price_status VARCHAR(50);",
        "ALTER TABLE ads ADD COLUMN IF NOT EXISTS market_average_price NUMERIC(10, 2);",
        "ALTER TABLE ads ADD COLUMN IF NOT EXISTS deviation_pct NUMERIC(10, 4);",
        "ALTER TABLE ads ADD COLUMN IF NOT EXISTS comparables_count INTEGER;",
        "ALTER TABLE ads ADD COLUMN IF NOT EXISTS confidence_level VARCHAR(50);",
        "ALTER TABLE ads ADD COLUMN IF NOT EXISTS matching_level_used INTEGER;",
        "ALTER TABLE ads ADD COLUMN IF NOT EXISTS calculated_at TIMESTAMP;"
    ]
    for cmd in commands:
        db.execute(text(cmd))
    db.commit()
    
    from market_analysis_service import MarketAnalysisService
    svc = MarketAnalysisService()
    background_tasks.add_task(svc.run_batch, db)
    
    return {"status": "success", "message": "Columns added and background analysis started."}
"""
    content += "\n" + endpoint_code
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Endpoint added")
