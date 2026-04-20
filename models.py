from sqlalchemy import Column, Integer, String, Text, DECIMAL, ForeignKey, TIMESTAMP, Boolean, Enum, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from database import Base
import enum

# Association Tables for Many-to-Many Relationships
category_tags = Table(
    'category_tags',
    Base.metadata,
    Column('category_id', Integer, ForeignKey('categories.id', ondelete="CASCADE"), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete="CASCADE"), primary_key=True)
)

ad_tags = Table(
    'ad_tags',
    Base.metadata,
    Column('ad_id', Integer, ForeignKey('ads.id', ondelete="CASCADE"), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete="CASCADE"), primary_key=True)
)

user_viewed_ads = Table(
    'user_viewed_ads',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete="CASCADE"), primary_key=True),
    Column('ad_id', Integer, ForeignKey('ads.id', ondelete="CASCADE"), primary_key=True),
    Column('viewed_at', TIMESTAMP, server_default=func.now(), onupdate=func.now())
)

class City(Base):
    __tablename__ = "cities"
    id = Column(Integer, primary_key=True, index=True)
    name_ar = Column(String(100), nullable=False)
    name_en = Column(String(100), nullable=False)
    
    regions = relationship("Region", back_populates="city")

class Region(Base):
    __tablename__ = "regions"
    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(Integer, ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)
    name_ar = Column(String(100), nullable=False)
    name_en = Column(String(100), nullable=False)
    latitude = Column(DECIMAL(10, 8), nullable=True)
    longitude = Column(DECIMAL(11, 8), nullable=True)
    
    city = relationship("City", back_populates="regions")

class Directorate(Base):
    __tablename__ = "directorates"
    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(Integer, ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)
    name_ar = Column(String(100), nullable=False)

class Village(Base):
    __tablename__ = "villages"
    id = Column(Integer, primary_key=True, index=True)
    directorate_id = Column(Integer, ForeignKey("directorates.id", ondelete="CASCADE"), nullable=False)
    name_ar = Column(String(100), nullable=False)

class Basin(Base):
    __tablename__ = "basins"
    id = Column(Integer, primary_key=True, index=True)
    village_id = Column(Integer, ForeignKey("villages.id", ondelete="CASCADE"), nullable=False)
    name_ar = Column(String(100), nullable=False)

class NeighborhoodSector(Base):
    __tablename__ = "neighborhood_sectors"
    id = Column(Integer, primary_key=True, index=True)
    basin_id = Column(Integer, ForeignKey("basins.id", ondelete="CASCADE"), nullable=False)
    name_ar = Column(String(100), nullable=False)
class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    
    # Relationships
    categories = relationship("Category", secondary=category_tags, back_populates="linked_tags")
    ads = relationship("Ad", secondary=ad_tags, back_populates="linked_tags")

class SourceType(str, enum.Enum):
    ORGANIC_USER = "ORGANIC_USER"
    SCRAPER_BOT = "SCRAPER_BOT"
    SCRAPER = "SCRAPER"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    mobile_number = Column(String(20), unique=True, index=True, nullable=True) # Mobile OTP priority
    username = Column(String(50), unique=True, nullable=True) # Optional now
    email = Column(String(100), unique=True, nullable=True) # Optional now
    hashed_password = Column(String(255), nullable=True) # Optional now
    phone = Column(String(20))
    avatar_url = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Profile & Premium Features
    user_type = Column(String(50), default="private")
    cover_image_url = Column(Text, nullable=True)
    overall_rating = Column(DECIMAL(3, 2), default=0.0)
    response_rate = Column(Integer, default=100)
    average_response_time = Column(String(50), default="Typically replies within 1 hour")
    trust_score = Column(Integer, default=50)
    followers_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    is_email_verified = Column(Boolean, default=False)
    is_phone_verified = Column(Boolean, default=False)
    is_identity_verified = Column(Boolean, default=False)
    location = Column(String(100), default="")
    
    # KYC Identity Verification
    full_name = Column(String(100), nullable=True)
    national_id = Column(String(20), nullable=True, unique=True)
    date_of_birth = Column(String(20), nullable=True)
    id_expiry_date = Column(String(20), nullable=True)
    identity_document_url = Column(Text, nullable=True)
    liveness_passed = Column(Boolean, default=False)
    face_similarity_score = Column(DECIMAL(5, 2), nullable=True)
    verification_status = Column(String(20), default="pending") # pending, verified, rejected
    
    # Advanced Profile Ext.
    bio = Column(Text, nullable=True)
    preferred_contact = Column(String(50), nullable=True)
    languages_spoken = Column(JSONB, nullable=True)
    deals_completed = Column(Integer, default=0)
    cancellation_rate = Column(Integer, default=0)
    buyer_satisfaction = Column(Integer, default=0)
    shop_name = Column(String(100), nullable=True)
    business_policy = Column(Text, nullable=True)
    shop_location = Column(Text, nullable=True)
    shop_hours = Column(String(100), nullable=True)
    
    ads = relationship("Ad", back_populates="owner")
    metrics = relationship("UserMetric", back_populates="user", uselist=False)
    reviews_received = relationship("UserReview", foreign_keys="UserReview.target_user_id", back_populates="target_user")
    reviews_given = relationship("UserReview", foreign_keys="UserReview.reviewer_id", back_populates="reviewer")
    viewed_ads = relationship("Ad", secondary=user_viewed_ads, back_populates="viewed_by_users")

class UserReview(Base):
    __tablename__ = "user_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    target_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating = Column(DECIMAL(3, 2), nullable=False)
    text = Column(Text, nullable=False)
    tags = Column(JSONB, default=[]) # Qualitative tags like 'Fast responder'
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    target_user = relationship("User", foreign_keys=[target_user_id], back_populates="reviews_received")
    reviewer = relationship("User", foreign_keys=[reviewer_id], back_populates="reviews_given")

class UserMetric(Base):
    __tablename__ = "user_metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    saved_items = Column(Integer, default=0)
    recently_viewed = Column(Integer, default=0)
    active_ads = Column(Integer, default=0)

    user = relationship("User", back_populates="metrics")

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    icon_name = Column(String(50))
    color_hex = Column(String(10))
    background_url = Column(String(255))
    tag = Column(String(50))
    slugs = Column(JSONB)
    order_index = Column(Integer, default=0)

    ads = relationship("Ad", back_populates="category")
    children = relationship("Category", backref="parent", remote_side=[id])
    linked_tags = relationship("Tag", secondary=category_tags, back_populates="categories")

class Ad(Base):
    __tablename__ = "ads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"))
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    raw_description = Column(Text, nullable=True)
    price = Column(DECIMAL(10, 2), nullable=False)
    location = Column(Text, nullable=False)
    image_url = Column(Text)
    attributes = Column(JSONB)
    views = Column(Integer, default=0)
    is_hot = Column(Boolean, default=False)
    is_published = Column(Boolean, default=False)
    
    # My Ads / User Listings support fields
    expires_at = Column(TIMESTAMP, nullable=True)
    is_paused = Column(Boolean, default=False)
    is_sold = Column(Boolean, default=False)
    is_rejected = Column(Boolean, default=False)
    rejected_reason = Column(Text, nullable=True)
    is_boosted = Column(Boolean, default=False)
    boost_expiry = Column(TIMESTAMP, nullable=True)
    chats_count = Column(Integer, default=0)
    favorites_count = Column(Integer, default=0)
    
    # Scraper Support Fields
    source_type = Column(Enum(SourceType), default=SourceType.ORGANIC_USER)
    source_url = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="ads")
    category = relationship("Category", back_populates="ads")
    real_estate_detail = relationship("AdRealEstateDetail", back_populates="ad", uselist=False)
    linked_tags = relationship("Tag", secondary=ad_tags, back_populates="ads")
    viewed_by_users = relationship("User", secondary=user_viewed_ads, back_populates="viewed_ads")

    @property
    def image_urls(self):
        if self.attributes and isinstance(self.attributes, dict):
            return self.attributes.get("image_urls", [])
        return []

    @image_urls.setter
    def image_urls(self, value):
        if self.attributes is None:
            self.attributes = {}
        self.attributes = {**self.attributes, "image_urls": value}

    @property
    def phone_number(self):
        if self.attributes and isinstance(self.attributes, dict):
            return self.attributes.get("phone_number", None)
        return None

    @phone_number.setter
    def phone_number(self, value):
        if self.attributes is None:
            self.attributes = {}
        self.attributes = {**self.attributes, "phone_number": value}

    @property
    def rooms(self):
        if self.attributes and isinstance(self.attributes, dict):
            return self.attributes.get("rooms", None)
        return None

    @rooms.setter
    def rooms(self, value):
        if self.attributes is None:
            self.attributes = {}
        self.attributes = {**self.attributes, "rooms": value}

class AdRealEstateDetail(Base):
    __tablename__ = "ad_real_estate_details"

    id = Column(Integer, primary_key=True, index=True)
    ad_id = Column(Integer, ForeignKey("ads.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    bathrooms = Column(Integer, nullable=True)
    furnished = Column(String(50), nullable=True)
    build_area = Column(Integer, nullable=True)
    floor = Column(String(50), nullable=True)
    building_age = Column(String(50), nullable=True)
    rent_duration = Column(String(50), nullable=True)
    view_orientation = Column(String(50), nullable=True)

    key_features = Column(JSONB, default=[])
    additional_features = Column(JSONB, default=[])
    nearby_locations = Column(JSONB, default=[])

    ad = relationship("Ad", back_populates="real_estate_detail")

class LiveTicker(Base):
    __tablename__ = "live_tickers"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

class Story(Base):
    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    image_url = Column(Text, nullable=False)
    title = Column(String(100))
    created_at = Column(TIMESTAMP, server_default=func.now())

    owner = relationship("User")

class SavedGroup(Base):
    __tablename__ = "saved_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    url = Column(Text, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    category = relationship("Category")

class OtpCode(Base):
    __tablename__ = "otp_codes"

    id = Column(Integer, primary_key=True, index=True)
    mobile_number = Column(String(20), index=True, nullable=False)
    otp_code = Column(String(10), nullable=False)
    expires_at = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    attempts = Column(Integer, default=0)
    ip_address = Column(String(50))

class RateLimitLog(Base):
    __tablename__ = "rate_limit_logs"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(50), index=True, nullable=True)
    mobile_number = Column(String(20), index=True, nullable=True)
    endpoint = Column(String(100), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    target_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=True)
    type = Column(String(50), nullable=True)          # e.g. "new_ad", "message", "system"
    reference_id = Column(Integer, nullable=True)      # e.g. ad_id, message_id
    is_read = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    target_user = relationship("User")

class UserDeviceToken(Base):
    __tablename__ = "user_device_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    fcm_token = Column(Text, nullable=False, unique=True)
    device_type = Column(String(20), nullable=True)    # "android", "ios", "web"
    created_at = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User")

class UserActivityLog(Base):
    __tablename__ = "user_activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    action_type = Column(String(100), nullable=False) # e.g. "APPLY_FILTER", "VIEW_CATEGORY", "SEARCH"
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    filters_json = Column(JSONB, nullable=True) # stores applied filter state
    created_at = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User")
    category = relationship("Category")

class SavedFilter(Base):
    __tablename__ = "saved_filters"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=True)
    name = Column(String(100), nullable=True)
    min_price = Column(DECIMAL(10, 2), nullable=True)
    max_price = Column(DECIMAL(10, 2), nullable=True)
    tags = Column(JSONB, nullable=True)      # ["مفروشة", "عمان", ...]
    locations = Column(JSONB, nullable=True) # ["عمان", "صويلح", ...]
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User")
    category = relationship("Category")

class AITrainingLog(Base):
    __tablename__ = "ai_training_logs"

    id = Column(Integer, primary_key=True, index=True)
    post_text = Column(Text, nullable=False)
    status = Column(String(50), nullable=False) # e.g. success, failed, rejected
    ai_model = Column(String(100), nullable=True) # e.g. gemini-2.5-flash-lite, deepseek-chat
    ai_output = Column(JSONB, nullable=True)     # Stores the parsed dictionary from AI
    raw_response = Column(Text, nullable=True)   # Stores the exact unparsed text returned by AI for training
    reason = Column(Text, nullable=True)         # E.g. "Seeking apartment (category_id=0)"
    created_at = Column(TIMESTAMP, server_default=func.now())
