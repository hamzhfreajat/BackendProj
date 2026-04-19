import logging
from database import engine
from models import AITrainingLog

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Ensuring AITrainingLog table exists in the database...")
    try:
        AITrainingLog.__table__.create(engine, checkfirst=True)
        logger.info("Successfully created/verified ai_training_logs table!")
    except Exception as e:
        logger.error(f"Failed to create table: {e}")

if __name__ == "__main__":
    main()
