import os

content = """
class AdSearchIndex(Base):
    __tablename__ = "ad_search_index"
    
    ad_id = Column(Integer, ForeignKey("ads.id", ondelete="CASCADE"), primary_key=True)
    category_id = Column(Integer, nullable=False, index=True)
    city_id = Column(Integer, nullable=True, index=True)
    region_id = Column(Integer, nullable=True, index=True)
    deal_type = Column(String(20), nullable=True) # SALE, RENT, BOTH
    property_type = Column(String(50), nullable=True)
    price = Column(DECIMAL(12, 2), nullable=True)
    bedrooms = Column(Integer, nullable=True)
    bathrooms = Column(Integer, nullable=True)
    furnished = Column(Boolean, nullable=True)
    build_area = Column(DECIMAL(10, 2), nullable=True)
    floor_number = Column(Integer, nullable=True)
    is_hot = Column(Boolean, default=False)
    is_boosted = Column(Boolean, default=False)
    attributes_jsonb = Column(JSONB, nullable=True)
    search_text = Column(Text, nullable=True)
    search_vector = Column(TSVECTOR, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    ad = relationship("Ad")
"""

with open("d:/open/classifieds-app/backend/models.py", "a", encoding="utf-8") as f:
    f.write(content)
