with open('schemas.py', 'a', encoding='utf-8') as f:
    f.write('''
# AD REPORT SCHEMAS
class AdReportCreate(BaseModel):
    reason: str
    comments: Optional[str] = None

class AdReportOut(BaseModel):
    id: int
    ad_id: int
    user_id: Optional[int] = None
    reason: str
    comments: Optional[str] = None
    status: str
    created_at: datetime
    
    # We can include ad title and username for dashboard convenience
    ad_title: Optional[str] = None
    reporter_name: Optional[str] = None

    class Config:
        from_attributes = True
''')
