import re

def update_models():
    filepath = 'D:/open/classifieds-app/backend/models.py'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if "market_price_status" in content:
        print("Columns already exist in models.py")
        return
        
    # We need to insert the columns into the Ad class.
    # Find the spot after cpc_bid = Column(DECIMAL(10, 2), default=0.00)
    target = "cpc_bid = Column(DECIMAL(10, 2), default=0.00)"
    
    columns_to_add = """
    cpc_bid = Column(DECIMAL(10, 2), default=0.00)
    
    market_price_status = Column(String(50), nullable=True)
    market_average_price = Column(DECIMAL(10, 2), nullable=True)
    deviation_pct = Column(DECIMAL(10, 4), nullable=True)
    comparables_count = Column(Integer, nullable=True)
    confidence_level = Column(String(50), nullable=True)
    matching_level_used = Column(Integer, nullable=True)
    calculated_at = Column(TIMESTAMP, nullable=True)
    """
    
    content = content.replace(target, columns_to_add)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("Updated models.py")

update_models()
