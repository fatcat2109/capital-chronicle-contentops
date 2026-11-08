from pathlib import Path
from datetime import datetime,timezone
from hashlib import sha256
import json,re
here=Path(__file__).resolve().parent
check=json.loads((here/'source-readiness.json').read_bytes())
prior=Path.cwd()/'docs/publisher/CC-124/run-20261108-0352'
old=json.loads((prior/'source-comparison.json').read_bytes())['searched_native_reports']
expected={r['path']:r['sha256'] for r in old}
nfp=Path(r'A:\Capital Chronicle\ResearchRuns\claude-main-research\20261106-nfp\dossier-20261106T093133Z')
sources=[nfp/name for name in ('primary-native.json','critical-native.json','owner-native.json','native-hybrid-decision.json','integrated-qualitative-evaluation.json')]
sources.extend(Path(r['path']) for r in check['latest_daily_main_reports'])
t2=Path(r'A:\Capital Chronicle\ResearchRuns\claude-main-research\t2-runs')
sources.extend(sorted(t2.glob('t2-*/t2-output.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:3])
keymatch=re.compile(r'scenario|probabil|invalidation|countercase|market_implication|^p_',re.I)
def walk(v,ptr=''):
    if isinstance(v,dict):
        for k,w in v.items():
            at=ptr+'/'+k
            if keymatch.search(k): yield {'pointer':at,'value':w}
            else: yield from walk(w,at)
    elif isinstance(v,list):
        for i,w in enumerate(v):yield from walk(w,ptr+'/'+str(i))
rows=[]
for path in sources:
    raw=path.read_bytes(); data=json.loads(raw); digest=sha256(raw).hexdigest()
    rows.append({'path':str(path),'sha256':digest,'modified_at_utc':datetime.fromtimestamp(path.stat().st_mtime,timezone.utc).isoformat(),'same_bytes_as_previous_search':expected.get(str(path))==digest if str(path) in expected else None,'keys':list(data),'matches':list(walk(data)),'theses_count':len(data.get('theses',[])),'not_taken_count':len(data.get('not_taken',[]))})
main=json.loads((here/'main-export-scenarios.json').read_bytes())['scenarios']
missing=sum(((row['value'] or {}).get('main_alternative') or {}).get('probability_pct') is None for row in main)
base_missing=sum(((row['value'] or {}).get('base_case') or {}).get('probability_pct') is None for row in main)
priorread=json.loads((prior/'source-readiness.json').read_bytes())
latest_same=check['latest_daily_main_reports'][0]['sha256']==priorread['latest_daily_main_reports'][0]['sha256']
brain=Path(r'A:\Capital Chronicle\ResearchRuns\claude-main-research\brain-runs')
brainrows=[]
for directory in sorted([p for p in brain.iterdir() if p.is_dir()],key=lambda p:p.stat().st_mtime,reverse=True)[:5]:
    children=[p.name for p in directory.iterdir() if p.is_file()]
    brainrows.append({'path':str(directory),'files':children,'has_full_native_return':any(p in children for p in ('owner-native.json','primary-native.json','synthesis-native.json')),'outcome_files':[p for p in children if p in ('PREPARE_REFUSED.json','OVERLAP_SKIPPED.json','STATUS.md','run.json')]})
backlog=Path(r'A:\Capital Chronicle\control-tower-reporting-closeout-20261018\docs\project_control_tower')
backlog_summary=[]
for name in ('BACKLOG.md','BACKLOG_ARCHIVE.md'):
    path=backlog/name
    lines=path.read_text(encoding='utf-8').splitlines()
    hits=[{'line':i+1,'text':line[:1500]} for i,line in enumerate(lines) if re.search(r'probabil|scenario',line,re.I) and re.search(r'CC-124|CC-330|CC-333|committee|alternative|Main',line,re.I)]
    backlog_summary.append({'path':str(path),'sha256':sha256(path.read_bytes()).hexdigest(),'match_count':len(hits),'matches':hits[:35]})
now=datetime.now(timezone.utc)
result={'observed_at_utc':now.isoformat(),'classification':'SOURCE_BLOCKED','first_cause':'JIM_DECISION_93_MAIN_SCENARIOS_INCOMPLETE','reason':'Jim decision 93 requires Main-supplied probabilities, confirmation, all six market implications and invalidation for 2-3 scenarios. Do not invent a complement or use conditional direction confidence as scenario probability.','export_scenarios':len(main),'export_missing_main_alternative_probability':missing,'export_missing_base_probability':base_missing,'latest_complete_daily_report_unchanged':latest_same,'searched_native_reports':rows,'brain_runs_checked':brainrows,'backlog_search':backlog_summary,'data_research_paths':[{'path':str(p),'exists':p.exists()} for p in (Path.cwd()/'data/research',Path(r'A:\Capital Chronicle\ContentOps\data\research'))],'source_facts_used_by':'Installed RetainedSourceResearch and Main export reader, source comparison before any writer or publish.','t2_output_comparison':'The latest three held T2 outputs are included with their exact content hashes and scenario/probability key search.','choice':'Preserve the exact NFP operation and pending writer; retain usable Main and BLS facts; make no incomplete public post.','next_actor':'Main report producer, then Codex Publisher','next_action':'Main supplies a dated post-release base case and alternative with explicit probabilities, confirmation, six-market implications and invalidation. Publisher consumes that version in the existing operation/source-review path.'}
(here/'source-comparison.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
assert missing==len(main) and len(main)>0
assert latest_same
assert all(r['same_bytes_as_previous_search'] for r in rows)
assert all(not r['matches'] for r in rows[11:])
print(json.dumps({'first_cause':result['first_cause'],'export_scenario_count':len(main),'missing_alternative_probability':missing,'missing_base_probability':base_missing,'unchanged_full_nfp_and_daily_reports':11,'unchanged_t2_outputs_without_scenarios':len(rows)-11,'brain_runs_checked':len(brainrows),'latest_daily_report_unchanged':latest_same,'artifact':str(here/'source-comparison.json')}))
