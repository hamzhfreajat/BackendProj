import json
import requests
import boto3
from sqlalchemy.orm import sessionmaker
from database import engine, SessionLocal
from models import Category

# Cloudflare R2 Config
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

BRAND_MAPPING = {
    "أبارث": "abarth",
    "أوبل": "opel",
    "أودي": "audi",
    "إنفينيتي": "infiniti",
    "استون مارتن": "aston-martin",
    "اكس بينج": "xpeng",
    "اكيورا": "acura",
    "الفا روميو": "alfa-romeo",
    "ام جي": "mg",
    "ايسوزو": "isuzu",
    "باجاني": "pagani",
    "بايك": "baic",
    "بنتلي": "bentley",
    "بوجاتي": "bugatti",
    "بورش": "porsche",
    "بولستار": "polestar",
    "بي ام دبليو": "bmw",
    "بي واي دي": "byd",
    "بيجو": "peugeot",
    "تاتا": "tata",
    "تويوتا": "toyota",
    "تيسلا": "tesla",
    "جاك": "jac",
    "جاكوار": "jaguar",
    "جيب": "jeep",
    "جيلي": "geely",
    "جينيسيس": "genesis",
    "داسيا": "dacia",
    "دايهاتسو": "daihatsu",
    "دودج": "dodge",
    "رولز رویس": "rolls-royce",
    "رينو": "renault",
    "سكودا": "skoda",
    "سمارت": "smart",
    "سوبارو": "subaru",
    "سوزوكي": "suzuki",
    "سيات": "seat",
    "شانجان": "changan",
    "شيري": "chery",
    "شيفروليه": "chevrolet",
    "فورد": "ford",
    "فولفو": "volvo",
    "فولكسفاغن": "volkswagen",
    "فيات": "fiat",
    "فيراري": "ferrari",
    "كاديلاك": "cadillac",
    "كرايسلر": "chrysler",
    "كيا": "kia",
    "لادا": "lada",
    "لامبورغيني": "lamborghini",
    "لاند روفر": "land-rover",
    "لانسيا": "lancia",
    "لكزس": "lexus",
    "لوتس": "lotus",
    "لينكولن": "lincoln",
    "مازدا": "mazda",
    "مازيراتي": "maserati",
    "مرسيدس بنز": "mercedes-benz",
    "مكلارين": "mclaren",
    "ميتسوبيشي": "mitsubishi",
    "ميني": "mini",
    "نيسان": "nissan",
    "هافال": "haval",
    "هامر": "hummer",
    "هوندا": "honda",
    "هيونداي": "hyundai",
    "ارك فوكس": "arcfox",
    "اس دبليو ام": "swm",
    "افاتار": "avatr",
    "اكسيد": "exeed",
    "ايران خودرو": "ikco",
    "ايفيكو": "iveco",
    "اينوس": "ineos",
    "ايه إم سي": "amc",
    "باو": "baojun",
    "بروتون": "proton",
    "بريليانس": "brilliance",
    "بستيون": "bestune",
    "بورجوارد": "borgward",
    "بونتياك": "pontiac",
    "بويك": "buick",
    "تام": "tam",
    "تانك": "tank",
    "جاي ام اي في": "jmev",
    "جاي ام سي": "jmc",
    "جايكو": "jaecoo",
    "جريت وول": "great-wall",
    "جيتور": "jetour",
    "دايو": "daewoo",
    "دايون": "dayun",
    "دونج فينج": "dongfeng",
    "دي اف اس كي": "dfsk",
    "دي اف ام": "dongfeng",
    "ديبال": "deepal",
    "دينزا": "denza",
    "رايزنج": "rising",
    "ربدان": "rabdan",
    "روكس": "rox",
    "روي": "roewe",
    "ريهاي": "rihai",
    "زد إكس اوتو": "zx-auto",
    "زوتي": "zotye",
    "زيكر": "zeekr",
    "ساب": "saab",
    "ساتورن": "saturn",
    "سامسونج": "renault-samsung",
    "سانغ يونغ": "ssangyong",
    "ساوايست": "soueast",
    "سايبا": "saipa",
    "سبايكر": "spyker",
    "ستيروين": "citroen",
    "سكاي ويل": "skywell",
    "سيريس": "seres",
    "سينوترك": "sinotruk",
    "سيون": "scion",
    "فاو": "faw",
    "فوتون": "foton",
    "فورثينج": "forthing",
    "في جي في": "vgv",
    "كايي": "kaiyi",
    "كوبرا": "cupra",
    "كوينيجسيج": "koenigsegg",
    "لوسيد": "lucid",
    "لوكسجين": "luxgen",
    "ليب موتور": "leapmotor",
    "ليفان": "lifan",
    "لينج بوكس": "lingbox",
    "ماروتي سوزوكي": "maruti-suzuki",
    "ماكسيوس": "maxus",
    "ماهيندرا": "mahindra",
    "ميركوري": "mercury",
    "نيتا": "neta",
    "هاوتاي": "hawtai",
    "هونج تشي": "hongqi",
    "هونغهاي": "honghai",
    "وولينغ": "wuling",
    "ويلتميستر": "weltmeister",
    "يودو": "yudo",
    "آي إم": "im",
    "آيتو": "aito",
}

def upload_to_r2(content, file_name):
    s3_client.put_object(
        Bucket=R2_BUCKET_NAME,
        Key=file_name,
        Body=content,
        ContentType="image/png"
    )
    return f"{R2_PUBLIC_URL}/{file_name}"

def main():
    db = SessionLocal()
    categories = db.query(Category).filter(
        Category.parent_id.in_([101, 102]),
        Category.icon_name.is_(None) # Only process those that are missing
    ).all()
    
    print(f"Found {len(categories)} missing categories")
    updated_count = 0
    for cat in categories:
        slug = BRAND_MAPPING.get(cat.name)
        if not slug:
            continue
            
        url = f"https://raw.githubusercontent.com/filippofilip95/car-logos-dataset/master/logos/optimized/{slug}.png"
        print(f"Fetching logo for {slug}...")
        
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                file_name = f"logos/{slug}.png"
                public_url = upload_to_r2(resp.content, file_name)
                
                cat.icon_name = public_url
                db.commit()
                print(f"Success: {slug}")
                updated_count += 1
            else:
                print(f"Failed: {slug} (Status: {resp.status_code})")
        except Exception as e:
            print(f"Error with {slug}: {e}")

    print(f"Finished uploading and updating {updated_count} logos!")
    db.close()

if __name__ == '__main__':
    main()
