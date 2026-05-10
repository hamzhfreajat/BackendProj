import sys
sys.path.append('d:\\open\\classifieds-app\\backend')
from search_parser import QueryParserService
from search_service import SearchService
from database import SessionLocal

db = SessionLocal()

print("Testing BEFORE adding to LOCATIONS")
q = "شقق بالجاردنز"
parsed = QueryParserService.parse(q)
print("Parsed:", parsed.dict())
print("Count:", SearchService.count_properties(db, q))

# Now add to locations
QueryParserService.LOCATIONS.append("الجاردنز")
QueryParserService.LOCATIONS.append("الصويفية")
QueryParserService.LOCATIONS.append("ماركا")
QueryParserService.LOCATIONS.append("طبربور")
QueryParserService.LOCATIONS.append("سحاب")
QueryParserService.LOCATIONS.append("الرابية")
QueryParserService.LOCATIONS.append("وسط البلد")
QueryParserService.LOCATIONS.append("اللويبدة")
QueryParserService.LOCATIONS.append("السلط")
QueryParserService.LOCATIONS.append("جبل الحسين")
QueryParserService.LOCATIONS.append("أم أذينة")
QueryParserService.LOCATIONS.append("دير غبار")
QueryParserService.LOCATIONS.append("أبو علندا")
QueryParserService.LOCATIONS.append("مادبا")
QueryParserService.LOCATIONS.append("البحر الميت")
QueryParserService.LOCATIONS.append("الكرك")
QueryParserService.LOCATIONS.append("الطفيلة")
QueryParserService.LOCATIONS.append("عجلون")
QueryParserService.LOCATIONS.append("معان")
QueryParserService.LOCATIONS.append("الأغوار")
QueryParserService.LOCATIONS.append("شفا بدران")
QueryParserService.LOCATIONS.append("الغور")
QueryParserService.LOCATIONS.append("المفرق")
QueryParserService.LOCATIONS.append("جرش")
QueryParserService.LOCATIONS.append("القسطل")
QueryParserService.LOCATIONS.append("العبدلي")
QueryParserService.LOCATIONS.append("الرصيفة")
QueryParserService.LOCATIONS.append("أبو نصير")
QueryParserService.LOCATIONS.append("الكرسي")

print("\nTesting AFTER adding to LOCATIONS")
parsed2 = QueryParserService.parse(q)
print("Parsed2:", parsed2.dict())
print("Count2:", SearchService.count_properties(db, q))

