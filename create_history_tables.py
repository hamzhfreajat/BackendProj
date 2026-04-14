import models
from database import engine

print("Applying new schemas to PostgreSQL database (if they don't exist)...")
models.Base.metadata.create_all(bind=engine)
print("Successfully generated user_viewed_ads_table.")
