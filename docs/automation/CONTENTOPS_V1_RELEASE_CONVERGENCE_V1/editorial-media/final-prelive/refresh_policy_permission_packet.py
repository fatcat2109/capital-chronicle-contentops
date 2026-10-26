"""Refresh pre-writer deterministic packet with previously verified rights, no new source."""
import json
import shutil
from pathlib import Path
from scripts.run_native_desktop_editorial import operation
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn
ROOT=Path(__file__).resolve().parent
b=json.loads((ROOT/'policy/binding.json').read_bytes())
store=ContentOpsDurableStore(b['store_path'],auto_migrate=False)
turn=NativeDesktopTurn(store,run_id=b['run_id'],output_dir=b['output_dir'],owner_manual_validation=True)
if turn.frozen_request('write') or turn._get('write','response'):
    raise ValueError('UNFROZEN_PREWRITER_PERMISSION_REPAIR_ONLY')
out=Path(b['output_dir']).resolve()
history=out/'source-recovery-history'/'verified-permission-projection'
history.mkdir(parents=True,exist_ok=True)
for name in ('simple_gemini_evidence_v1.json','editorial_media_plan_required.json'):
    src=out/name;dst=history/name
    if src.is_file() and not dst.exists():
        if not dst.resolve().is_relative_to(out):raise ValueError('HISTORY_OUTSIDE_OPERATION')
        src.rename(dst)
result=operation(b)
(ROOT/'policy/rights-projection-refresh.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
shutil.copyfile(Path(b['output_dir'])/'editorial_media_plan_required.json',ROOT/'policy/editorial_media_plan_required.json')
print(json.dumps(result))
