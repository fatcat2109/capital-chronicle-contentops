"""One-shot preparation of exact existing-owner operations; no model or public calls."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[4]
PROFILE=json.loads((REPO/'config/native_desktop_operator_profile_v1.json').read_bytes())
cases={
 'policy':('v1-prelive-fed-policy',"Prepare one useful dated government-policy explainer from admitted prelive-fed-implementation-20260916 and supporting goal21-fed-policy. Explain how the September 16, 2026 decision is implemented through reserve-balance interest, standing repo and reverse repo rates effective September 17. This is a dated policy case, not a current decision or a new market observation. Use the responsible official Kevin Warsh's authentic separately cleared May 22 archive photo, with role verified against the September FOMC minutes; it is not a photograph of that decision. Plan a meaningful exact-source comparison of the three announced administered rates, not an invented past series or forecast. Keep decision, implementation, bank/cash transmission, countercase, uncertainty and next source-bound observation clear. Read the existing accepted public Main manifest first and retain independent official-source lineage. No proprietary numeric inference or public action."),
 'gold':('v1-prelive-gold-oct23',"Prepare one genuinely current attributed report analysis from admitted prelive-gold-20261023: Reuters' October 23, 2026 gold report syndicated by Kitco. The reported spot-gold observation is 15:20 UTC, publisher machine publication 19:17:01 UTC and update 19:18:51 UTC; capture is later and is not the event. Explain why a reported fall in gold alongside silver, platinum and palladium complicates a simple safe-haven story; price co-movement alone does not prove oil or monetary policy caused it. Use a useful exact-source quantitative comparison and a separately licensed authentic archive gold photograph, no copied publisher image. Preserve single Reuters-origin report truth and uncertainty in all packages, and the current story/update identity. This is distinct from the five October21 revisions. Read current accepted public Main manifest first, preserve independent source lineage and do not invent Main numeric authority, a fresh official confirmation or a market close.")}

def invoke(folder, args):
 folder.mkdir(exist_ok=True)
 proc=subprocess.run([sys.executable,'-X','utf8','scripts/run_native_desktop_editorial.py',*args],cwd=REPO,text=True,capture_output=True)
 (folder/'native-start.stdout.txt').write_text(proc.stdout,encoding='utf-8')
 (folder/'native-start.stderr.txt').write_text(proc.stderr,encoding='utf-8')
 if proc.returncode: raise RuntimeError(proc.stderr[-2200:])
 value=json.loads(proc.stdout)
 (folder/'native-start.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
 return value

for slug,(op,request) in cases.items():
 folder=ROOT/slug
 folder.mkdir(exist_ok=True)
 (folder/'owner-request.txt').write_text(request,encoding='utf-8')
 result=invoke(folder,['newsroom','--operation-id',op,'--request-file',str(folder/'owner-request.txt'),'--report-only'])
 output=Path(PROFILE['editorial_output_root'])/op
 for name in ('binding.json','desktop_request_select.json'):
  if (output/name).exists():shutil.copyfile(output/name,folder/name)
 print(json.dumps({'slug':slug,'operation':op,'result':result}),flush=True)

for slug,identity in [('tesla','44561321bc94626d866e87985e4778435e0a497417f2a76fb3cbdd830b6b6705'),
                      ('southwest','857f96cfc5871ccf64e49d33ba1224ccbc275ff7f9b91ef1061982d7d4572f2f')]:
 folder=ROOT/(slug+'-r2');folder.mkdir(exist_ok=True);op='v1-prelive-'+slug+'-r2'
 reason=('Material reader-facing source-note repair only: replace the internal known-at/evidence-cutoff microsecond chronology and process-heavy retained-review language with a concise source date and honest unpublished editorial-revision/no-new-reporting note. Keep detailed capture/known-at/cutoff times in the immutable source record rather than public prose. Keep the reported facts, claims, meaningful single-source Reuters uncertainty, analytical thesis, strongest countercase, useful watchpoint, source date and SEO coherent. Do not introduce fresh evidence, currentness, independent confirmation or a new economic observation. Reuse the same exact inspected lawful photograph and source-bound chart/data. Preserve all C9 article/review/preparation bytes and the same story/update chain. No change beyond a useful bounded prose revision is requested.')
 prior={'run_id':'v1-media-'+slug+'-r1','article_identity':identity,'reason':reason}
 (folder/'editorial-revision-request.json').write_text(json.dumps(prior,indent=2)+'\n',encoding='utf-8')
 result=invoke(folder,['editorial-revision','--operation-id',op,'--response',str(folder/'editorial-revision-request.json')])
 output=Path(PROFILE['editorial_output_root'])/op
 for name in ('binding.json','desktop_request_select.json'):
  if (output/name).exists():shutil.copyfile(output/name,folder/name)
 print(json.dumps({'slug':slug+'-r2','operation':op,'result':result}),flush=True)
