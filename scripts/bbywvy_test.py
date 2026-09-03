import time, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = "StarpowerTechnology/BbyWVY-360m"
print("loading tokenizer...", flush=True)
tokenizer = AutoTokenizer.from_pretrained(model_id)
print("loading model...", flush=True)
t0 = time.time()
model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float16).to("cuda")
model.eval()
print(f"loaded in {time.time()-t0:.1f}s, params: {sum(p.numel() for p in model.parameters())/1e6:.0f}M", flush=True)

def chat(messages, max_new_tokens=120, temperature=0.7, top_p=0.95):
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    t0 = time.time()
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=max_new_tokens,
                              temperature=temperature, top_p=top_p, do_sample=True,
                              pad_token_id=tokenizer.eos_token_id)
    dt = time.time() - t0
    gen = out[0][inputs["input_ids"].shape[-1]:]
    text = tokenizer.decode(gen, skip_special_tokens=True)
    ntok = len(gen)
    print(f"  [{ntok} tok in {dt:.1f}s = {ntok/max(dt,1e-6):.0f} tok/s]")
    return text

tests = [
    ("identity", [{"role": "system", "content": "u are WVY. be curious, honest, and conversational."},
                  {"role": "user", "content": "Who are you?"}]),
    ("quantum-honesty", [{"role": "system", "content": "u are WVY. be curious, honest, and conversational."},
                         {"role": "user", "content": "what do u know about quantum physics?"}]),
    ("casual", [{"role": "user", "content": "wassup bro what are u thinking about?"}]),
    ("factual", [{"role": "user", "content": "What is the capital of France?"}]),
    ("math", [{"role": "user", "content": "If a train goes 60 km/h for 2.5 hours, how far does it travel?"}]),
    ("followup", [{"role": "user", "content": "I just started learning guitar, any tips?"}]),
]
for name, msgs in tests:
    print(f"\n=== {name} ===")
    print("USER:", msgs[-1]["content"])
    print("WVY:", chat(msgs))
