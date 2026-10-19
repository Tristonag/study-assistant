"""Step 0: check that everything is set up before you write any project code.

Run:  python check_setup.py
It checks your Python version, your .gitignore, your API key, one text call and
one image call, and prints what each call would cost. Safe to run any time.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ok = True


def good(msg):
    print(f"  OK    {msg}")


def bad(msg):
    global ok
    ok = False
    print(f"  FIX   {msg}")


print("\n1. Python")
v = sys.version_info
if v >= (3, 10):
    good(f"Python {v.major}.{v.minor}")
else:
    bad(f"Python {v.major}.{v.minor} is too old. Install Python 3.13 from python.org.")
if sys.prefix == sys.base_prefix:
    bad("You're not inside the virtual environment. Run: source .venv/Scripts/activate")
else:
    good("virtual environment is active")

print("\n2. .gitignore (keeps your key and the slides off GitHub)")
gitignore = ROOT / ".gitignore"
lines = {line.strip() for line in gitignore.read_text(encoding="utf-8").splitlines()} if gitignore.exists() else set()
for needed in (".env", ".venv", "data/", "eval/own.csv"):
    if needed in lines or needed.rstrip("/") in lines or needed + "/" in lines:
        good(f"{needed} is ignored")
    else:
        bad(f"add a line `{needed}` to .gitignore")

print("\n3. API key")
try:
    from dotenv import load_dotenv
except ImportError:
    sys.exit("  FIX   Packages missing. Run: pip install -r requirements.txt")
load_dotenv(ROOT / ".env")
key = os.getenv("GEMINI_API_KEY", "")
if not (ROOT / ".env").exists():
    bad("no .env file. Run: cp .env.example .env   then paste your key into it")
elif not key or key.startswith("paste"):
    bad("GEMINI_API_KEY in .env is empty. Paste your key after the = (no quotes, no spaces)")
else:
    good(f"key found ({key[:4]}... , {len(key)} characters). Never paste it anywhere else.")

if not ok:
    sys.exit("\nFix the lines marked FIX, then run this again.")

print("\n4. A text call")
import llm  # noqa: E402  (imported here so the checks above run even if llm.py breaks)
import config  # noqa: E402

text, usage = llm.ask("Reply with exactly these words: setup works", max_output_tokens=50)
print(f"  Model said: {text!r}")
print(f"  {usage['input_tokens']} tokens in, {usage['output_tokens']} out, would cost ${usage['cost_usd']:.6f} on the paid tier")

print("\n5. An image call (the model has to read a number off a picture)")
import pymupdf  # noqa: E402

doc = pymupdf.open()
page = doc.new_page(width=480, height=200)
page.insert_text((40, 110), "The secret number is 4712", fontsize=26)
png = page.get_pixmap(dpi=96).tobytes("png")
text, usage = llm.ask("What is the secret number in this image? Reply with the number only.",
                      model=config.CAPTION_MODEL, images=[png], max_output_tokens=50)
print(f"  Model said: {text!r}")
print(f"  {usage['input_tokens']} tokens in, {usage['output_tokens']} out, would cost ${usage['cost_usd']:.6f} on the paid tier")
if "4712" in text:
    good("vision works")
else:
    bad("the model didn't read the number. Send Claude a screenshot of this output.")

print("\nAll good! Commit everything (your .env stays on your PC). Next: step 1, ingest.py." if ok
      else "\nAlmost: fix the lines marked FIX above.")
