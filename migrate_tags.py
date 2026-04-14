from database import SessionLocal, Base, engine
from models import Category, Tag

def migrate_tags():
    # Make sure tables exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        categories = db.query(Category).all()
        print(f"Found {len(categories)} categories")
        
        tags_processed = 0
        tags_created = 0
        
        for category in categories:
            if category.slugs and 'ar' in category.slugs and isinstance(category.slugs['ar'], list):
                tag_names = category.slugs['ar']
                
                for tag_name in tag_names:
                    tags_processed += 1
                    # Find or create tag
                    tag = db.query(Tag).filter(Tag.name == tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.add(tag)
                        db.commit() # Commit to get ID
                        db.refresh(tag)
                        tags_created += 1
                    
                    # Link to category if not already linked
                    if tag not in category.linked_tags:
                        category.linked_tags.append(tag)
                
        db.commit()
        print(f"Migration completed. Processed {tags_processed} tag items, created {tags_created} unique database tags.")
    except Exception as e:
        print(f"Error migrating tags: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting tag migration...")
    migrate_tags()
