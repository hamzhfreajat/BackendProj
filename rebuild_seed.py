import codecs
import json

with codecs.open('seed_categories.py', 'r', encoding='utf-8') as f:
    orig = f.read()

end_marker = '(106208, 1062, "أرقام نادرة", None, None, None, None, None),'
last_good = orig.find(end_marker)
if last_good == -1:
    print("Could not find end marker")
    exit(1)

clean_part1 = orig[:last_good + len(end_marker)] + '\n'

with codecs.open('footer.txt', 'r', encoding='utf-8') as f:
    footer = f.read()

models_output = []

brands_data = [
    {'id': '40391', 'label': 'QJmotor'}, {'id': '8682', 'label': 'Sym'}, {'id': '8680', 'label': 'إم في أجوستا'}, {'id': '13493', 'label': 'إنديان'}, {'id': '4531', 'label': 'ابريليا'}, {'id': '23582', 'label': 'الدكن'}, {'id': '19827', 'label': 'باجاج'}, {'id': '19865', 'label': 'باندا'}, {'id': '4535', 'label': 'بوجي'}, {'id': '23574', 'label': 'بولاريس'}, {'id': '4533', 'label': 'بي إم دبليو'}, {'id': '4553', 'label': 'بياجيو'}, {'id': '13489', 'label': 'بينيلي'}, {'id': '38719', 'label': 'تارو'}, {'id': '19799', 'label': 'تايجر'}, {'id': '4559', 'label': 'تريمف'}, {'id': '13490', 'label': 'تي في اس'}, {'id': '23580', 'label': 'جوني باغ'}, {'id': '13492', 'label': 'جيانشي'}, {'id': '13491', 'label': 'دايليم'}, {'id': '23584', 'label': 'دايونغ'}, {'id': '4539', 'label': 'دوكاتي'}, {'id': '14878', 'label': 'رويال انفيلد'}, {'id': '23578', 'label': 'زونتس'}, {'id': '24330', 'label': 'سانيا'}, {'id': '4557', 'label': 'سوزوكي'}, {'id': '8678', 'label': 'سي اف موتو'}, {'id': '23594', 'label': 'شارماكس'}, {'id': '43089', 'label': 'فوج'}, {'id': '4561', 'label': 'فيسبا'}, {'id': '8684', 'label': 'فيكتوري'}, {'id': '19781', 'label': 'كامكو'}, {'id': '4537', 'label': 'كان ام'}, {'id': '4547', 'label': 'كاواساكي'}, {'id': '4549', 'label': 'كاي تي ام'}, {'id': '19817', 'label': 'كي واي'}, {'id': '43135', 'label': 'لونسين'}, {'id': '4551', 'label': 'موتو جوزي'}, {'id': '19805', 'label': 'ناما'}, {'id': '4541', 'label': 'هارلي ديفيدسون'}, {'id': '19847', 'label': 'هاوجن'}, {'id': '4545', 'label': 'هايوسنج'}, {'id': '43275', 'label': 'هوسكفارنا'}, {'id': '4543', 'label': 'هوندا'}, {'id': '18839', 'label': 'هيرو'}, {'id': '23576', 'label': 'واي سي ار موتور'}, {'id': '4563', 'label': 'ياماها'}, {'id': '4565', 'label': 'اخرى'}
]

MODELS_MAP = {
    'هوندا': ['CBR', 'Gold Wing', 'CRF', 'Shadow', 'Africa Twin', 'PCX', 'Grom', 'Dio', 'Rebel', 'CB', 'أخرى'],
    'ياماها': ['YZF-R1', 'YZF-R6', 'YZF-R3', 'MT-09', 'MT-07', 'Tenere', 'XMAX', 'TMAX', 'FZ', 'أخرى'],
    'سوزوكي': ['GSX-R', 'Hayabusa', 'V-Strom', 'Boulevard', 'SV650', 'Gixxer', 'Burgman', 'أخرى'],
    'كاواساكي': ['Ninja', 'Z', 'Vulcan', 'Versys', 'KLR', 'KX', 'أخرى'],
    'بي إم دبليو': ['S1000', 'R1250', 'F850', 'G310', 'K1600', 'أخرى'],
    'هارلي ديفيدسون': ['Sportster', 'Softail', 'Touring', 'Street', 'Pan America', 'أخرى'],
    'دوكاتي': ['Panigale', 'Monster', 'Multistrada', 'Diavel', 'Scrambler', 'أخرى'],
    'كاي تي ام': ['Duke', 'Adventure', 'RC', 'EXC', 'SX', 'أخرى'],
    'ابريليا': ['RSV4', 'Tuono', 'RS', 'Tuareg', 'أخرى'],
    'تريمف': ['Bonneville', 'Tiger', 'Street Triple', 'Speed Triple', 'Rocket', 'أخرى'],
    'فيسبا': ['Primavera', 'Sprint', 'GTS', 'Elettrica', 'أخرى'],
    'تي في اس': ['Apache', 'Jupiter', 'NTORQ', 'Sport', 'أخرى'],
    'باجاج': ['Pulsar', 'Dominar', 'Avenger', 'Discover', 'CT', 'أخرى'],
    'سي اف موتو': ['NK', 'SR', 'MT', 'GT', 'Papio', 'أخرى'],
    'رويال انفيلد': ['Classic', 'Bullet', 'Himalayan', 'Interceptor', 'Continental GT', 'أخرى'],
    'Sym': ['Joyride', 'Cruisym', 'Maxsym', 'Jet', 'Symphony', 'أخرى'],
    'بينيلي': ['TRK', 'Leoncino', 'TNT', 'Imperiale', 'أخرى'],
    'إنديان': ['Scout', 'Chief', 'Chieftain', 'Roadmaster', 'FTR', 'أخرى'],
}
DEFAULT_MODELS = ['100cc - 200cc', '250cc - 400cc', '500cc - 750cc', '1000cc فما فوق', 'سكوتر', 'أخرى']

models_output.append('\n    # ═══════════════════════════════════════════════\n')
models_output.append('    # SIXTH-LEVEL — MOTORYCYCLE MODELS\n')
models_output.append('    # ═══════════════════════════════════════════════\n')

for pid in range(103101, 103116):
    for b_idx, brand in enumerate(brands_data):
        bid = int(str(pid) + f"{(b_idx+1):02d}")
        m_list = MODELS_MAP.get(brand['label'], DEFAULT_MODELS)
        for m_idx, m_name in enumerate(m_list):
            mid = int(str(bid) + f"{(m_idx+1):02d}")
            models_output.append(f'    ({mid}, {bid}, "{m_name}", None, None, None, None, None),\n')

models_output.append(']\n\n')

final_code = clean_part1 + "".join(models_output) + footer

with codecs.open('seed_categories.py', 'w', encoding='utf-8') as f:
    f.write(final_code)

print('Successfully rebuilt seed_categories.py with models!')
