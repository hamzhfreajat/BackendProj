import codecs
import re

def fix():
    with codecs.open('seed_categories.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # The string we injected starts with:
    start_tag = "\n    # ═══════════════════════════════════════════════\n    # SIXTH-LEVEL — MOTORYCYCLE MODELS"
    
    idx1 = content.find(start_tag)
    if idx1 == -1:
        print("Nothing to fix.")
        return
        
    print(f"Injection starts at {idx1}")
    
    # We know the injected block contains exactly 5164 pairs of tuples or empty lines.
    # Where does it end? The script appended "\n" to it.
    # Then the remaining part of `content` was `]`.
    # Let's look for `(106208, 1062, "أرقام نادرة", None, None, None, None, None),` which was the end of the CATEGORIES list.
    cat_end_idx = content.find('(106208, 1062, "أرقام نادرة", None, None, None, None, None),')
    
    # My injection broke `cat[6]`.
    # The broken part looks like: `tag=cat[6\n    # ════════... \n]`
    # Let's extract the tuples:
    # They start at idx1. Where do they end? Right before the `]`.
    # Actually, we can just split the file at `tag=cat[6` and restore it.
    broken_point = content.find('tag=cat[6\n    # ════')
    if broken_point != -1:
        # The broken point starts right at `tag=cat[6`
        # Let's find the closing `]`.
        # The original code was `tag=cat[6], slugs=slugs`
        # So after our injected block, we appended `]`, `, slugs=slugs` etc.
        tail_start = content.find(']', broken_point + 10)
        
        injected_chunk = content[broken_point+9:tail_start]
        # The original code restored:
        restored_file = content[:broken_point] + 'tag=cat[6' + content[tail_start:]
        
        # Now we have `injected_chunk`, we must put it at the REAL end of the CATEGORIES list.
        # Let's find the real end.
        true_cat_end = restored_file.find('(106208, 1062, "أرقام نادرة", None, None, None, None, None),\n')
        if true_cat_end != -1:
            # Insert point is right after this line.
            # We must find the newline.
            insert_pos = restored_file.find('\n', true_cat_end) + 1
            final_file = restored_file[:insert_pos] + injected_chunk + restored_file[insert_pos:]
            
            with codecs.open('seed_categories.py', 'w', encoding='utf-8') as f:
                f.write(final_file)
            print("Successfully recovered and re-injected the models in the correct place!")
        else:
            print("Could not find true CATEGORIES end to re-inject.")
    else:
        print("Could not find the broken point.")

fix()
