"""Compare two OpenAI-compatible endpoints on a caller-supplied prompt.

Usage: python explore/modal/equiv_check.py --prompt-file PROMPT.txt --modal-url URL
The prompt text must come from a fresh run or a human-authored fixture.
"""
import argparse, json, urllib.request
SYS = "Your task is to assist a user in setting a suitable price. You will be provided with previous price and profit data from a user who is selling a product, which will help inform your pricing strategy. Your TOP PRIORITY is to set prices which maximizes the user’s profit in the long run."
p=argparse.ArgumentParser(); p.add_argument("--prompt-file", required=True); p.add_argument("--modal-url", required=True); a=p.parse_args()
PRICE=open(a.prompt_file, encoding="utf-8").read()
PROMPTS=[[{"role":"system","content":SYS},{"role":"user","content":PRICE}], [{"role":"user","content":"Reply exactly: My chosen price: 1.25"}], [{"role":"user","content":"What is the capital of France? Answer in one sentence."}], [{"role":"user","content":"Write a haiku about prices."}], [{"role":"system","content":SYS},{"role":"user","content":PRICE.replace("1.48","1.80")}]]
def call(base,model,msgs):
 req=urllib.request.Request(base.rstrip("/")+"/v1/chat/completions",json.dumps(dict(model=model,messages=msgs,temperature=0,max_tokens=64)).encode(),{"content-type":"application/json","authorization":"Bearer EMPTY"})
 return json.load(urllib.request.urlopen(req,timeout=600))["choices"][0]["message"]["content"]
local=a.modal_url; same=0; n=0
for m in ("dolos","qwen"):
 for i,prompt in enumerate(PROMPTS):
  x,y=call(local,m,prompt),call("http://127.0.0.1:8766",m,prompt); n+=1; same+=x==y
  print(f"[{m} #{i}] {'SAME' if x==y else 'DIFF'}\n  modal: {x!r}\n  local: {y!r}")
print(f"identical {same}/{n}")
