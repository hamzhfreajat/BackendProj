import json
import requests
import boto3
from database import SessionLocal
from models import Category

R2_ACCESS_KEY_ID = "0e100733aeb20a80893ab9f24fcfb268"
R2_SECRET_ACCESS_KEY = "195b95b9e8fa268e7e03a38bcd1b19ef3f7e14ceeb90221f62e38821dd937090"
R2_BUCKET_NAME = "joapp-ads"
R2_ENDPOINT_URL = "https://eca032391478b97d195a13ea5a7adc1e.r2.cloudflarestorage.com"
R2_PUBLIC_URL = "https://pub-158212dafa5344d4bbf078a74da2305a.r2.dev"

s3_client = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT_URL,
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    region_name="auto"
)

DOMAIN_MAPPING = {
    "اس دبليو ام": "swm-motors.com",
    "افاتار": "avatr.com",
    "اينوس": "ineosgrenadier.com",
    "بايك": "baicintl.com",
    "تام": "tatamotors.com",
    "تانك": "tanksuv.com",
    "جاي ام اي في": "jmev.com",
    "جايكو": "jaecoo.com",
    "جي أيه سي": "gac-motor.com",
    "جي ايه سي": "gac-motor.com",
    "جي إم سي": "gmc.com",
    "دي اف اس كي": "dfsk.com",
    "ديبال": "deepal.com.cn",
    "دينزا": "denza.com",
    "رايزنج": "risingauto.com",
    "ربدان": "rabdan.com",
    "روكس": "roxmotor.com",
    "ريهاي": "rehai.com",
    "زد إكس اوتو": "zxauto.com.cn",
    "ساوايست  ": "soueast-motor.com",
    "سكاي ويل": "skywell.com",
    "سيريس": "seres.com",
    "فورثينج": "forthingmotor.com",
    "في جي في": "vgv.com",
    "كايي": "kaiyiauto.com",
    "لينج بوكس": "lingbox.com",
    "لينك اند كو": "lynkco.com",
    "ماروتي سوزوكي": "marutisuzuki.com",
    "نيتا": "hozonauto.com",
    "هونغهاي": "honghai.com",
    "يودو": "yudoauto.com",
    "آي إم": "immotors.com",
    "آيتو": "aito.auto"
}

def upload_to_r2(content, file_name):
    s3_client.put_object(Bucket=R2_BUCKET_NAME, Key=file_name, Body=content, ContentType="image/png")
    return f"{R2_PUBLIC_URL}/{file_name}"

def main():
    db = SessionLocal()
    categories = db.query(Category).filter(Category.parent_id.in_([101, 102]), Category.icon_name == None).all()
    
    print(f"Found {len(categories)} missing categories")
    updated = 0
    for cat in categories:
        domain = DOMAIN_MAPPING.get(cat.name)
        if not domain:
            continue
            
        url = f"https://t0.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=http://{domain}&size=128"
        
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200 and len(resp.content) > 100:
                slug = domain.split(".")[0]
                file_name = f"logos/{slug}_favicon.png"
                public_url = upload_to_r2(resp.content, file_name)
                
                cat.icon_name = public_url
                db.commit()
                # print(f"Success: {cat.name}")
                updated += 1
        except Exception as e:
            pass

    print(f"Finished uploading {updated} favicons!")
    db.close()

if __name__ == "__main__":
    main()
