import psycopg2

try:
    conn = psycopg2.connect(host='178.104.204.148', port='9000', dbname='cmnynjgg90003aumlerff4j9q', user='postgres', password='p2j9ggm6cWLAhhVTsbNzYFqK')
    cur = conn.cursor()
    
    cur.execute("SELECT id, location FROM ads WHERE location LIKE '%%،%%' OR location LIKE '%%,%%'")
    ads = cur.fetchall()
    
    fixed_count = 0
    city_names = {"عمان", "إربد", "اربد", "الزرقاء", "زرقاء", "المفرق", "مفرق", "جرش", "عجلون", "البلقاء", "مادبا", "الكرك", "كرك", "الطفيلة", "طفيلة", "معان", "العقبة", "عقبة", "محافظة العاصمة"}
    
    for ad_id, location in ads:
        if location:
            loc = location.replace("،", ",")
            parts = [p.strip() for p in loc.split(",")]
            if len(parts) == 2:
                # If the SECOND part is a city, it means it was saved backwards (Region, City)
                if parts[1] in city_names:
                    new_loc = f"{parts[1]}, {parts[0]}"
                    cur.execute("UPDATE ads SET location = %s WHERE id = %s", (new_loc, ad_id))
                    fixed_count += 1
                    print(f"Fixed ad {ad_id}")
                    
    conn.commit()
    print(f"Total existing ads fixed: {fixed_count}")
    
except Exception as e:
    print('ERROR:', e)
