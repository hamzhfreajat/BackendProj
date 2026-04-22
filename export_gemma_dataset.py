import json
import os
import pathlib
from dotenv import load_dotenv

# Load env variables so we connect to the right database
_this_dir = pathlib.Path(__file__).resolve().parent
load_dotenv(_this_dir / ".env", override=True)

from sqlalchemy.orm import Session
from database import SessionLocal
from models import AITrainingLog

from sqlalchemy import text

def export_dataset():
    db: Session = SessionLocal()
    
    # Query all successful extractions using raw SQL to avoid schema mismatch
    query = text("SELECT post_text, ai_output FROM ai_training_logs WHERE status='success'")
    logs = db.execute(query).fetchall()
    count = len(logs)
    print(f"Found {count} successful logs.")
    
    if count == 0:
        print("No successful logs found to export.")
        return
        
    output_file = "gemma_dataset.jsonl"
    from fb_batch_router import _GEMMA_SINGLE_PROMPT
    
    exported = 0
    with open(output_file, 'w', encoding='utf-8') as f:
        for row in logs:
            post_text = row[0]
            ai_output = row[1]
            
            if not post_text or not ai_output:
                continue
                
            prompt = _GEMMA_SINGLE_PROMPT.format(post_text=post_text)
            messages = [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": json.dumps(ai_output, ensure_ascii=False)}
            ]
            
            f.write(json.dumps({"messages": messages}, ensure_ascii=False) + '\n')
            exported += 1
            
    print(f"Successfully exported {exported} valid examples to {output_file}.")
    print("This file can be used to fine-tune Gemma using Unsloth or Hugging Face. Ensure you use the exact prompt format for inference.")

if __name__ == "__main__":
    export_dataset()
