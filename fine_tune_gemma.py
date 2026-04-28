"""
Gemma 2 Fine-Tuning Boilerplate using Unsloth
=============================================
Instructions:
1. Upload this script and `gemma_dataset.jsonl` to Google Colab or your Cloud GPU.
2. Install dependencies:
   !pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
   !pip install --no-deps trl peft accelerate bitsandbytes xformers
3. Run the script to export your model.
"""

from unsloth import FastLanguageModel
import torch
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments

# 1. Configuration
max_seq_length = 2048
dtype = None
load_in_4bit = True  # Use 4-bit quantization to save memory

# 2. Load Base Model
# Recommended starting model: Gemma-2-2b or Gemma-2-9b
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/gemma-2-2b-it-bnb-4bit",  # Instruct tuned 4-bit base
    max_seq_length=max_seq_length,
    dtype=dtype,
    load_in_4bit=load_in_4bit,
)

# 3. Add LoRA Adapters
model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=3407,
    use_rslora=False,
    loftq_config=None,
)

# 4. Prepare Dataset
# Format function using Gemma's instruct template
from unsloth.chat_templates import get_chat_template
tokenizer = get_chat_template(
    tokenizer,
    chat_template="gemma",
    mapping={"role": "role", "content": "content", "user": "user", "assistant": "model"},
)

def formatting_prompts_func(examples):
    convos = examples["messages"]
    texts = [tokenizer.apply_chat_template(convo, tokenize=False, add_generation_prompt=False) for convo in convos]
    return {"text": texts}

# Load the exported JSONL
dataset = load_dataset("json", data_files="gemma_dataset.jsonl", split="train")
dataset = dataset.map(formatting_prompts_func, batched=True)

# 5. Setup Trainer
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=max_seq_length,
    dataset_num_proc=2,
    packing=False, # Can make training 5x faster for short sequences
    args=TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=5,
        max_steps=60, # Adjust based on dataset size (e.g. 1-3 epochs)
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=1,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=3407,
        output_dir="outputs",
    ),
)

# 6. Train!
print("Starting fine-tuning...")
trainer_stats = trainer.train()
print("Training complete!")

# 7. Save and Export
output_model_name = "gemma-2-classifieds-model"
model.save_pretrained(f"{output_model_name}_lora")
tokenizer.save_pretrained(f"{output_model_name}_lora")

# To use with Ollama/LM Studio, export to GGUF
print("Exporting to GGUF format for local inference...")
try:
    model.save_pretrained_gguf(f"{output_model_name}", tokenizer, quantization_method="q4_k_m")
    print(f"Success! Model saved to {output_model_name}.gguf - you can now load this in LM Studio or Ollama.")
except Exception as e:
    print(f"Export warning: {e}")
