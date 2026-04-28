"""
Qwen 2.5 3B Fine-Tuning Boilerplate using Unsloth
=================================================
Instructions:
1. Open Google Colab (https://colab.research.google.com/)
2. Create a "New Notebook" and change the runtime to T4 GPU (Runtime -> Change runtime type -> T4 GPU).
3. Upload this script (`fine_tune_qwen.py`) AND your `gemma_dataset.jsonl` to the Colab files section (folder icon on the left).
4. Run the following installation code in the very first Colab cell:
   !pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
   !pip install --no-deps trl peft accelerate bitsandbytes xformers
5. Copy and paste the rest of this code into standard Colab cells and run it!
"""

from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template
import torch
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments

# 1. Configuration
max_seq_length = 2048
dtype = None
load_in_4bit = True  # Keep 4bit to fit inside free Colab T4 GPU

# 2. Load Base Qwen Model (This is specifically Qwen 2.5 3B Instruct)
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Qwen2.5-3B-Instruct-bnb-4bit", 
    max_seq_length=max_seq_length,
    dtype=dtype,
    load_in_4bit=load_in_4bit,
)

# Fix tokenizer mapping to match Qwen's ChatML chat template
tokenizer = get_chat_template(
    tokenizer,
    chat_template="chatml",
    mapping={"role": "role", "content": "content", "user": "user", "assistant": "assistant"}
)

# 3. Add LoRA Adapters (This makes the memory footprint super small)
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

# 4. Load your existing dataset!
def formatting_prompts_func(examples):
    texts = []
    # gemma_dataset.jsonl has a "messages" array (OpenAI format)
    for messages in examples["messages"]:
        # Let Unsloth auto-apply the correct model-specific ChatML formatting
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        texts.append(text)
    return {"text": texts}

# Assuming 'gemma_dataset.jsonl' is uploaded to the Colab environment
dataset = load_dataset("json", data_files={"train": "gemma_dataset.jsonl"}, split="train")
dataset = dataset.map(formatting_prompts_func, batched=True)

# 5. Start Training
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=max_seq_length,
    dataset_num_proc=2,
    packing=False,
    args=TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=5,
        max_steps=60, # Increase to 150-300 if you want it to learn it perfectly
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

trainer_stats = trainer.train()

# 6. Export the Model Locally as GGUF
print("Training Complete! Exporting to Q4_K_M GGUF format for your laptop...")

model.save_pretrained_gguf("qwen-classified-model", tokenizer, quantization_method="q4_k_m")

print("Export Done. You can now download the qwen-classified-model-unsloth.Q4_K_M.gguf file from Colab!")
