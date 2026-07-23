import sys

with open("fb_publisher_router.py", "r", encoding="utf-8") as f:
    content = f.read()

old_generate = """
    for i, ad in enumerate(ads, 1):
        price_str = f"{ad.price} دينار" if ad.price else "تواصل لمعرفة السعر"
        title = ad.title[:50] + "..." if ad.title and len(ad.title) > 50 else (ad.title or "عقار")
        
        # We explicitly WANT individual links here since the user wants to copy/paste it
        msg += f"{i}. {title}\\n💰 السعر: {price_str}\\n🔗 التفاصيل: https://share.sooq-com.com/ad/{ad.id}\\n\\n"
        
    msg += "تصفح المزيد على تطبيق وموقع سوقكم! ✨"
    
    if ads and len(ads) > 0:
        main_link = f"https://share.sooq-com.com/ad/{ads[0].id}"
    else:
        main_link = "https://share.sooq-com.com/"

    return {"text": msg, "main_link": main_link, "count": actual_count}
"""

new_generate = """
    fmt = req.format if hasattr(req, 'format') and req.format else "catalog"

    for i, ad in enumerate(ads, 1):
        price_str = f"{ad.price} دينار" if ad.price else "تواصل لمعرفة السعر"
        title = ad.title[:50] + "..." if ad.title and len(ad.title) > 50 else (ad.title or "عقار")
        
        if fmt in ["images", "text_only", "link"]:
            # no individual links
            msg += f"{i}. {title}\\n💰 السعر: {price_str}\\n\\n"
        else:
            # We explicitly WANT individual links here since the user wants to copy/paste it
            msg += f"{i}. {title}\\n💰 السعر: {price_str}\\n🔗 التفاصيل: https://share.sooq-com.com/ad/{ad.id}\\n\\n"
        
    msg += "تصفح المزيد على تطبيق وموقع سوقكم! ✨"
    
    if ads and len(ads) > 0:
        main_link = f"https://share.sooq-com.com/ad/{ads[0].id}"
    else:
        main_link = "https://share.sooq-com.com/"
        
    if fmt in ["link", "text_link_catalog", "text_link_images"]:
        msg += f"\\nالرابط الأساسي: {main_link}"

    return {"text": msg, "main_link": main_link, "count": actual_count}
"""

content = content.replace(old_generate.strip(), new_generate.strip())

with open("fb_publisher_router.py", "w", encoding="utf-8") as f:
    f.write(content)
