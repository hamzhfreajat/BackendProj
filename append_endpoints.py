with open('main.py', 'a', encoding='utf-8') as f:
    f.write('''
# ---------------------------------------------------------
# AD REPORTING ENDPOINTS
# ---------------------------------------------------------
@app.post("/api/ads/{ad_id}/report")
def report_ad(
    ad_id: int, 
    report: schemas.AdReportCreate,
    current_user: models.User = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    ad = db.query(models.Ad).filter(models.Ad.id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")
        
    user_id = current_user.id if current_user else None
    
    new_report = models.AdReport(
        ad_id=ad_id,
        user_id=user_id,
        reason=report.reason,
        comments=report.comments
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    return {"status": "success", "message": "Report submitted successfully"}

@app.get("/api/dashboard/reports", response_model=List[schemas.AdReportOut])
def get_dashboard_reports(
    admin_user: models.User = Depends(auth.get_current_admin),
    db: Session = Depends(get_db)
):
    reports = db.query(models.AdReport).order_by(models.AdReport.created_at.desc()).all()
    
    # Enrich with ad title and reporter name
    result = []
    for r in reports:
        out = schemas.AdReportOut.model_validate(r)
        if r.ad:
            out.ad_title = r.ad.title
        if r.user:
            out.reporter_name = r.user.full_name or r.user.username
        result.append(out)
        
    return result
''')
