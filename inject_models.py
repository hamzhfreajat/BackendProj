import re

# Dictionary of brands
brands_data = [
    {"id": "40391", "label": "QJmotor"},
    {"id": "8682", "label": "Sym"},
    {"id": "8680", "label": "إم في أجوستا"},
    {"id": "13493", "label": "إنديان"},
    {"id": "4531", "label": "ابريليا"},
    {"id": "23582", "label": "الدكن"},
    {"id": "19827", "label": "باجاج"},
    {"id": "19865", "label": "باندا"},
    {"id": "4535", "label": "بوجي"},
    {"id": "23574", "label": "بولاريس"},
    {"id": "4533", "label": "بي إم دبليو"},
    {"id": "4553", "label": "بياجيو"},
    {"id": "13489", "label": "بينيلي"},
    {"id": "38719", "label": "تارو"},
    {"id": "19799", "label": "تايجر"},
    {"id": "4559", "label": "تريمف"},
    {"id": "13490", "label": "تي في اس"},
    {"id": "23580", "label": "جوني باغ"},
    {"id": "13492", "label": "جيانشي"},
    {"id": "13491", "label": "دايليم"},
    {"id": "23584", "label": "دايونغ"},
    {"id": "4539", "label": "دوكاتي"},
    {"id": "14878", "label": "رويال انفيلد"},
    {"id": "23578", "label": "زونتس"},
    {"id": "24330", "label": "سانيا"},
    {"id": "4557", "label": "سوزوكي"},
    {"id": "8678", "label": "سي اف موتو"},
    {"id": "23594", "label": "شارماكس"},
    {"id": "43089", "label": "فوج"},
    {"id": "4561", "label": "فيسبا"},
    {"id": "8684", "label": "فيكتوري"},
    {"id": "19781", "label": "كامكو"},
    {"id": "4537", "label": "كان ام"},
    {"id": "4547", "label": "كاواساكي"},
    {"id": "4549", "label": "كاي تي ام"},
    {"id": "19817", "label": "كي واي"},
    {"id": "43135", "label": "لونسين"},
    {"id": "4551", "label": "موتو جوزي"},
    {"id": "19805", "label": "ناما"},
    {"id": "4541", "label": "هارلي ديفيدسون"},
    {"id": "19847", "label": "هاوجن"},
    {"id": "4545", "label": "هايوسنج"},
    {"id": "43275", "label": "هوسكفارنا"},
    {"id": "4543", "label": "هوندا"},
    {"id": "18839", "label": "هيرو"},
    {"id": "23576", "label": "واي سي ار موتور"},
    {"id": "4563", "label": "ياماها"},
    {"id": "4565", "label": "اخرى"}
]

MODELS_MAP = {
    "هوندا": ["CBR", "Gold Wing", "CRF", "Shadow", "Africa Twin", "PCX", "Grom", "Dio", "Rebel", "CB", "أخرى"],
    "ياماها": ["YZF-R1", "YZF-R6", "YZF-R3", "MT-09", "MT-07", "Tenere", "XMAX", "TMAX", "FZ", "أخرى"],
    "سوزوكي": ["GSX-R", "Hayabusa", "V-Strom", "Boulevard", "SV650", "Gixxer", "Burgman", "أخرى"],
    "كاواساكي": ["Ninja", "Z", "Vulcan", "Versys", "KLR", "KX", "أخرى"],
    "بي إم دبليو": ["S1000", "R1250", "F850", "G310", "K1600", "أخرى"],
    "هارلي ديفيدسون": ["Sportster", "Softail", "Touring", "Street", "Pan America", "أخرى"],
    "دوكاتي": ["Panigale", "Monster", "Multistrada", "Diavel", "Scrambler", "أخرى"],
    "كاي تي ام": ["Duke", "Adventure", "RC", "EXC", "SX", "أخرى"],
    "ابريليا": ["RSV4", "Tuono", "RS", "Tuareg", "أخرى"],
    "تريمف": ["Bonneville", "Tiger", "Street Triple", "Speed Triple", "Rocket", "أخرى"],
    "فيسبا": ["Primavera", "Sprint", "GTS", "Elettrica", "أخرى"],
    "تي في اس": ["Apache", "Jupiter", "NTORQ", "Sport", "أخرى"],
    "باجاج": ["Pulsar", "Dominar", "Avenger", "Discover", "CT", "أخرى"],
    "سي اف موتو": ["NK", "SR", "MT", "GT", "Papio", "أخرى"],
    "رويال انفيلد": ["Classic", "Bullet", "Himalayan", "Interceptor", "Continental GT", "أخرى"],
    "Sym": ["Joyride", "Cruisym", "Maxsym", "Jet", "Symphony", "أخرى"],
    "بينيلي": ["TRK", "Leoncino", "TNT", "Imperiale", "أخرى"],
    "إنديان": ["Scout", "Chief", "Chieftain", "Roadmaster", "FTR", "أخرى"],
}
DEFAULT_MODELS = ["100cc - 200cc", "250cc - 400cc", "500cc - 750cc", "1000cc فما فوق", "سكوتر", "أخرى"]

def generate_models(brand_id_base, brand_name):
    # Determine the model names array to use
    models_list = MODELS_MAP.get(brand_name, DEFAULT_MODELS)
    
    tuples = []
    for m_idx, m_name in enumerate(models_list):
        # We append a 2-digit index to the end of the brand's ID to form the model's ID.
        # Since brand ID is 8 digits like 10310101, model ID is 10 digits 1031010101.
        # This assumes no more than 99 models per brand, which is perfectly safe.
        mid = int(str(brand_id_base) + f"{(m_idx+1):02d}")
        
        row = f'    ({mid}, {brand_id_base}, "{m_name}", None, None, None, None, None),'
        tuples.append(row)
        
    return tuples

def main():
    target_file = 'seed_categories.py'
    
    with open(target_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Locate the end of the CATEGORIES list.
    # It ends with `]` probably.
    last_bracket_idx = content.rfind(']')
    if last_bracket_idx == -1:
        print("ERROR: Could not find closing bracket for CATEGORIES.")
        return
        
    parents = range(103101, 103116)
    
    all_rows = []
    all_rows.append("")
    all_rows.append("    # ═══════════════════════════════════════════════")
    all_rows.append("    # SIXTH-LEVEL — MOTORYCYCLE MODELS")
    all_rows.append("    # ═══════════════════════════════════════════════")
    
    for pid in parents:
        for b_idx, brand in enumerate(brands_data):
            # Same deterministic brand ID logic
            bid = int(str(pid) + f"{(b_idx+1):02d}")
            
            # Now generate its models
            all_rows.extend(generate_models(bid, brand['label']))
            all_rows.append("") # space
            
    print(f"Generating {len(all_rows)} lines of brand models.")
    
    new_str = "\n".join(all_rows) + "\n"
    
    new_content = content[:last_bracket_idx] + new_str + content[last_bracket_idx:]
    
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print("SUCCESS: Injected motorcycle models.")

if __name__ == '__main__':
    main()
