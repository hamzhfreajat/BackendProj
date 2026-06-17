from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:123456@localhost:5432/classifieds_db')
with engine.connect() as con:
    con.execute(text('TRUNCATE TABLE telemetry_events RESTART IDENTITY CASCADE;'))
    con.commit()
    print('Truncated telemetry_events successfully')
