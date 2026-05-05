with open('auth.py', 'a', encoding='utf-8') as f:
    f.write('''
# Admin Dependency
def get_current_admin(current_user: models.User = Depends(get_current_user)):
    if current_user.user_type != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges")
    return current_user
''')
