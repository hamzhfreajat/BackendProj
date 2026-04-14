import json
import re

json_data = """{
    "status": 200,
    "hash": "d0e2c447901c202fe032b0bef77f4373",
    "data": {
        "values": [
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
    }
}"""

def main():
    data = json.loads(json_data)["data"]["values"]
    parents = range(103101, 103116)
    
    lines = []
    lines.append("")
    lines.append("    # ═══════════════════════════════════════════════")
    lines.append("    # FIFTH-LEVEL — MOTORYCYCLE BRANDS")
    lines.append("    # ═══════════════════════════════════════════════")
    
    for pid in parents:
        for idx, brand in enumerate(data):
            # Form an ID by appending 2 digits (e.g. 10310101)
            new_id = int(str(pid) + f"{(idx+1):02d}")
            label = brand['label'].replace('"', '\\"') # escape just in case
            lines.append(f'    ({new_id}, {pid}, "{label}", None, None, None, None, None),')
    
    # insert after (103115, 1031, "معدلة / مخصصة", None, None, None, None, None),
    
    target_file = 'seed_categories.py'
    with open(target_file, 'r', encoding='utf-8') as f:
        content = f.read()

    search_str = '(103115, 1031, "معدلة / مخصصة", None, None, None, None, None),'
    idx = content.find(search_str)
    
    if idx == -1:
        print("COULD NOT FIND INSERTION POINT!")
        return
    
    insert_pos = idx + len(search_str)
    
    new_content = content[:insert_pos] + "\n" + "\n".join(lines) + content[insert_pos:]
    
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print("SUCCESS: Injected motorcycle brands.")

if __name__ == '__main__':
    main()
