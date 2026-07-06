import re

# Update auth.py
with open("auth.py", "r", encoding="utf-8") as f:
    auth_content = f.read()

# Add request: Request to google_auth
auth_content = re.sub(
    r'def google_auth\((.*?)\):',
    r'def google_auth(\1, request: Request = None):',
    auth_content
)

# Set ip_address in google_auth (user creation)
auth_content = re.sub(
    r'user = models.User\(\s*email=email,\s*avatar_url=idinfo.get\(\'picture\'\),\s*is_email_verified=True,\s*username=email.split\(\'@\'\)\[0\]\s*\)',
    r"user = models.User(\n                email=email,\n                avatar_url=idinfo.get('picture'),\n                is_email_verified=True,\n                username=email.split('@')[0],\n                ip_address=get_real_ip(request) if request else None\n            )",
    auth_content
)

# Add request: Request to facebook_auth
auth_content = re.sub(
    r'def facebook_auth\((.*?)\):',
    r'def facebook_auth(\1, request: Request = None):',
    auth_content
)

# Set ip_address in facebook_auth
auth_content = re.sub(
    r'user = models.User\(\s*email=email,\s*full_name=full_name,\s*avatar_url=avatar_url,\s*is_email_verified=True,\s*username=email.split\(\'@\'\)\[0\]\s*\)',
    r"user = models.User(\n                email=email,\n                full_name=full_name,\n                avatar_url=avatar_url,\n                is_email_verified=True,\n                username=email.split('@')[0],\n                ip_address=get_real_ip(request) if request else None\n            )",
    auth_content
)

# Add request: Request to apple_auth
auth_content = re.sub(
    r'def apple_auth\((.*?)\):',
    r'def apple_auth(\1, request: Request = None):',
    auth_content
)

# Set ip_address in apple_auth
auth_content = re.sub(
    r'user = models.User\(\s*email=email,\s*full_name=full_name,\s*is_email_verified=True,\s*username=email.split\(\'@\'\)\[0\] if email else f"apple_user_\{apple_sub\[:8\]\}"\s*\)',
    r'user = models.User(\n                email=email,\n                full_name=full_name,\n                is_email_verified=True,\n                username=email.split(\'@\')[0] if email else f"apple_user_{apple_sub[:8]}",\n                ip_address=get_real_ip(request) if request else None\n            )',
    auth_content
)

with open("auth.py", "w", encoding="utf-8") as f:
    f.write(auth_content)


# Update main.py create_ad and create_ad_draft
with open("main.py", "r", encoding="utf-8") as f:
    main_content = f.read()

# Add request: Request to create_ad
main_content = re.sub(
    r'def create_ad\(\s*ad: schemas.AdCreate,\s*background_tasks: BackgroundTasks,\s*current_user: models.User = Depends\(auth.get_current_user\),\s*db: Session = Depends\(get_db\)\s*\):',
    r'def create_ad(\n    ad: schemas.AdCreate, \n    background_tasks: BackgroundTasks,\n    current_user: models.User = Depends(auth.get_current_user),\n    db: Session = Depends(get_db),\n    request: Request = None\n):',
    main_content
)

main_content = re.sub(
    r'db_ad = models.Ad\(\s*\*\*ad_data,\s*user_id=user_id\s*\)',
    r'db_ad = models.Ad(\n        **ad_data,\n        user_id=user_id,\n        ip_address=get_real_ip(request) if request else None\n    )',
    main_content
)

# Add request: Request to create_ad_draft
main_content = re.sub(
    r'def create_ad_draft\(\s*ad_draft: schemas.AdDraftCreate,\s*current_user: models.User = Depends\(auth.get_current_user\),\s*db: Session = Depends\(get_db\)\s*\):',
    r'def create_ad_draft(\n    ad_draft: schemas.AdDraftCreate,\n    current_user: models.User = Depends(auth.get_current_user),\n    db: Session = Depends(get_db),\n    request: Request = None\n):',
    main_content
)

main_content = re.sub(
    r'db_ad = models.Ad\(\*\*ad_data, user_id=user_id\)',
    r'db_ad = models.Ad(**ad_data, user_id=user_id, ip_address=get_real_ip(request) if request else None)',
    main_content
)

with open("main.py", "w", encoding="utf-8") as f:

    f.write(main_content)

print("Updated auth.py and main.py successfully")
