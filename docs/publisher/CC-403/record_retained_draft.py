"""One decision-114 draft from held public spans; never a publication operation."""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from live_contentops.article_scenarios_v1 import WRITER_GUIDANCE as SCENARIO_GUIDANCE
from live_contentops.daily_note_first_draft_v1 import prepare_first_draft
from live_contentops.public_instruments_v1 import GUIDANCE as INSTRUMENT_GUIDANCE
from live_contentops.reader_article_contract_v1 import GUIDANCE, contract_for
from live_contentops.v1_simple_gemini_newsroom_v1 import _worker_prompt


def main():
    request = Path("A:/Capital Chronicle/Runtime/ContentOps/daily_app_outputs/owner-manual/cc124-pre-us-wrap-20261109-v1/desktop_request_write.json")
    capture = Path("A:/Capital Chronicle/ResearchRuns/claude-main-research/daily-research-portfolio-279805139/requests/request-91a0ed68b1eb799e/capture.json")
    raw, capture_raw = request.read_bytes(), capture.read_bytes()
    governed = deepcopy(json.loads(raw)["governed_input"])
    governed.pop("editorial_media_plan", None)
    governed["selected_candidate"]["reader_format"] = "DAILY_NOTE"
    clock = json.loads(capture_raw)["known_at_utc"]
    governed["source_pack"][0].update(data_cutoff_utc=clock, data_clock_binding=[{
        "path": str(capture), "sha256": sha256(capture_raw).hexdigest(), "field": "/known_at_utc", "value": clock}])
    governed["reader_article_contract"] = contract_for(governed)
    folder = Path(__file__).resolve().parent / "retained-draft"
    folder.mkdir(exist_ok=True)
    source = {"observed_at_utc": datetime.now(timezone.utc).isoformat(),
              "held_request_path": str(request), "held_request_sha256": sha256(raw).hexdigest(),
              "data_cutoff_utc": clock, "request_cutoff_utc": governed["cutoff_utc"],
              "reason": "Held 9 November public spans exercise the restored decision-114 first-draft consumer. CC-403's next-daily publication acceptance remains separate.",
              "publication_operation_created": False, "historical_request_changed": False}
    (folder / "source.json").write_text(json.dumps(source, indent=2), encoding="utf-8")
    prompt = (_worker_prompt(governed) + "\n" + SCENARIO_GUIDANCE + "\n" + INSTRUMENT_GUIDANCE + "\n" + GUIDANCE
              + "\nUse only the supplied historical 9 November cutoff and facts. Do not present them as current on 10 November.")
    record = prepare_first_draft(governed, prompt, output_dir=folder)
    summary = {k: record.get(k) for k in ("status", "model", "effort", "configuration_status", "started_at_utc",
        "ended_at_utc", "prompt_sha256", "output_sha256", "artifact_path", "checks", "cause")}
    summary.update(source_data_cutoff_utc=clock, publication_operation_created=False)
    (folder / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
