from pathlib import Path
import json,re,hashlib,shutil,sys
from datetime import datetime,timezone
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
H=Path('docs/publisher/CC-341/resume-20261109');H.mkdir(exist_ok=True)
def save(p,v): p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
P=Path(r'A:\Capital Chronicle\control-tower-reporting-closeout-20261018\docs\project_control_tower\report_upgrade_review_20261105\strategy\WEEKEND_WRAP_20261109_R2_SCENARIOS.md')
raw=P.read_bytes();assert hashlib.sha256(raw).hexdigest()=='edbdad3496c5f81c3d889513201032af7aac9a99ccfaf5ff36dc38c95ad63c1e';t=raw.decode('utf-8-sig');a=t.index('## 2.');z=t.index('## 7.')
fr=[]
for m in re.finditer(r'[^|\n]+',t[a:z]):
 s,e=a+m.start(),a+m.end()
 if not t[s:e].strip(' -:'):continue
 while e-s>1700:
  b=t.rfind(' ',s,s+1700);fr.append({'start':s,'end':b});s=b+1
 fr.append({'start':s,'end':e})
base=json.loads(Path('docs/publisher/CC-341/source/index.json').read_bytes())['records'][0]
spec={**base,'headline_id':'cc341-weekend-wrap-r2-scenarios-20261109','headline_text':'Weekend wrap R2: Capital Chronicle model-estimate scenarios 55% base, 25% escalation, 20% deal through Friday 13 November, plus attributed Nvidia update','known_at_utc':'2026-11-08T23:26:00Z','revision_at_utc':datetime.now(timezone.utc).isoformat(),'source_url':'urn:cc-public-report:cc341:weekend-wrap:r2:20261109','passages':[{'source_path':str(P),'source_sha256':hashlib.sha256(raw).hexdigest(),'fragments':fr[i:i+12]} for i in range(0,len(fr),12)]}
S=H/'source';S.mkdir(exist_ok=True)
if (S/'index.json').exists():
 held=json.loads((S/'index.json').read_bytes())
 assert held['records'][1]['passages']==spec['passages'], 'Source changed; retain the dated edition.'
 spec=held['records'][1]
else:
 save(S/'index.json',{'schema_version':'contentops.retained_source_research.v1','records':[base,spec]})
r=RetainedSourceResearch(S);assert not r.gaps,r.gaps
save(H/'source-admission.json',{'consumer':'RetainedSourceResearch','source_sha256':hashlib.sha256(raw).hexdigest(),'research_revision':r.revision,'document_ids':list(r.records),'gaps':r.gaps,'known_at_utc':spec['known_at_utc'],'original_operation_unchanged':True,'revision_reason':'Ops reopened with material new analysis and Nvidia fact after the former cutoff; preserve prior zero-write frozen opportunity; new dated edition uses new operation identity.'})
profile=json.loads(Path('config/native_desktop_operator_profile_v1.json').read_bytes());profile['research_editions_root']+=[str(S.resolve())];save(H/'profile.json',profile)
request=Path('docs/publisher/CC-341/request.txt').read_text(encoding='utf-8')+'\nOps Product reopened CC-341 9 Nov 06:26 GMT+7. Use new dated R2 scenario edition cc341-weekend-wrap-r2-scenarios-20261109, admitted through RetainedSourceResearch, alongside original public draft cc341-weekend-wrap-20261109. Preserve public-ready draft; replace Scenarios with section 5 of WEEKEND_WRAP_20261109_R2_SCENARIOS.md, add section 6 Nvidia paragraph after the Three other stories mattered paragraph. Scenario probabilities 55/25/20 are Capital Chronicle model estimates through Fri 13 Nov; section 2/3 supply exact confirmation/invalidation/six-market bindings. No portfolio/broker execution details. Publish promptly, Sunday evening ET until 05:00Z, Monday morning ET after; deadline 10:00Z 9 Nov. No invented reopen line. Fresh USOIL TradingView image. Prior operation never wrote and its frozen input predates R2, so this material revision uses operation cc341-weekend-wrap-20261109-r2, sole publication identity for the revised article.'
(H/'request.txt').write_text(request,encoding='utf-8')
capture_root=Path(r'A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc341-weekend-wrap-20261109-r2\source-captures');capture_root.mkdir(exist_ok=True)
shutil.copyfile(r'C:\Users\bullw\AppData\Local\BrowserClaw\Application\155.0.8317.26\.browseros\tool-output\read-1794181101285-ecd12b87-7388-4bcb-9f74-dc909a27daf8.md',capture_root/'cnbc-source-read.md')
print(json.dumps({'admitted':list(r.records),'gaps':r.gaps,'fragments':len(fr)}))
