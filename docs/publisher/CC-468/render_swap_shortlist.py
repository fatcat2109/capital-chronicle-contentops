"""Render the local review page; opens no site, writes no message."""
from html import escape
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
document = json.loads((ROOT / "swap-shortlist.json").read_bytes())
cards = []
for index, row in enumerate(document["candidates"]):
    cards.append(f'''<article><div class="label">{index + 1:02d} · {escape(row['audience_label'])}</div>
<h2>{escape(row['name'])}</h2><p>{escape(row['fit'])}</p>
<p class="source">Last visible post: {escape(row['latest_visible_date'])} · {escape(row['latest_visible_title'])}</p>
<nav><a target="_blank" rel="noopener" href="{escape(row['publication_url'])}">Publication</a>
<a target="_blank" rel="noopener" href="{escape(row['activity_source_url'])}">Activity</a>
<a target="_blank" rel="noopener" href="{escape(row['size_source_url'])}">Audience label</a></nav>
<details><summary>Prepared message from Jim</summary><textarea readonly id="draft{index}">{escape(row['message'])}</textarea></details>
<button data-index="{index}">Copy message and open author</button><span class="feedback" id="status{index}"></span></article>''')
page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CC-468 · Recommendation swap shortlist</title><style>
*{box-sizing:border-box}body{margin:0;background:#f5f1e9;color:#182b34;font:17px/1.55 system-ui,sans-serif}
main{max-width:1120px;margin:auto;padding:45px 24px}.eyebrow,.label{color:#667c80;font:600 12px/1.5 system-ui;letter-spacing:.08em;text-transform:uppercase}
h1{font:44px/1.1 Georgia,serif;max-width:800px;margin:12px 0 20px}header p{max-width:820px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,420px),1fr));gap:20px;margin-top:32px}
article{background:#fffdf8;padding:25px;border:1px solid #d6ded9;border-radius:10px;display:flex;flex-direction:column}h2{font:28px/1.15 Georgia;margin:10px 0}p{margin:10px 0}.source{font-size:13px;color:#576c73}
nav{display:flex;gap:18px;flex-wrap:wrap;font-size:14px;margin:12px 0}a{color:#165d82}button{cursor:pointer;border:0;border-radius:6px;background:#165d82;color:white;font:600 15px system-ui;padding:13px 16px;margin-top:18px}
textarea{display:block;width:100%;min-height:220px;padding:12px;font:15px/1.5 system-ui;border:1px solid #cbd6d3;margin-top:12px;resize:vertical}details{margin-top:auto;padding-top:10px}.feedback{font-size:13px;margin-top:8px;color:#496c57}
@media(max-width:600px){main{padding:28px 16px}h1{font-size:34px}article{padding:20px}}
</style><main><header><div class="eyebrow">Capital Chronicle · CC-468 · Private preparation</div>
<h1>Ten newsletters to consider for recommendation swaps</h1>
<p>Each message is ready for Jim to review. The button copies its text and opens the verified author profile. Jim opens Message, pastes and sends it. This page sends nothing.</p>
<p class="source">Public pages checked on 12 November 2026, GMT+7. Audience labels are platform observations, not exact current list sizes; “over” labels are lower bounds. Every candidate has a recent visible archive entry. No recommendation agreement is claimed.</p>
</header><div class="grid">''' + "".join(cards) + '''</div></main><script>
const candidates = ''' + json.dumps([{k: row[k] for k in ("profile_url", "message")} for row in document["candidates"]], ensure_ascii=True).replace("<", "\\u003c") + ''';
for(const button of document.querySelectorAll('button[data-index]'))button.addEventListener('click',async()=>{
const index=Number(button.dataset.index), row=candidates[index];
const opened=window.open(row.profile_url,'_blank','noopener');
try{await navigator.clipboard.writeText(row.message);document.getElementById('status'+index).textContent='Copied. Only Jim sends.';}
catch{const box=document.getElementById('draft'+index);box.closest('details').open=true;box.focus();box.select();document.getElementById('status'+index).textContent='Copy the selected message, then use the author profile. Only Jim sends.';}
});</script></html>'''
(ROOT / "swap-review.html").write_text(page, encoding="utf-8")
print(json.dumps({"candidates": len(cards), "path": str(ROOT / "swap-review.html")}))
