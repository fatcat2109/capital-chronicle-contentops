"""CC-425's bounded, file-only table check before first publication.

Read the producer's bound inputs without updating its files or store. Reuse its
source decoders and CC-011 spread; independently recompute the selected returns.
The supplied article is checked through the actual publication table validator.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib
import json
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from live_contentops.cpi_reaction_page_v1 import validate_bound_tables, tables, reader_names, digest


def sample_releases(events, seed=425):
    ordered = sorted(e["release_utc"] for e in events)
    if len(set(ordered)) != len(ordered) or len(ordered) < 8:
        raise ValueError("CPI_VERIFICATION_REQUIRES_EIGHT_DISTINCT_RELEASES")
    return sorted(random.Random(seed).sample(ordered[:-3], 5)) + ordered[-3:]


def recompute_market(symbol, indexed, released, as_of, cpi):
    """Re-select one series; arithmetic uses decoded/store prices, not data.json."""
    targets = cpi.endpoints(released)
    stamp = int(released.timestamp())
    choices = [(key, rows) for key, rows in indexed.items()
               if key[0] == symbol and stamp in rows and not rows[stamp].get("conflict")]
    choices.sort(key=lambda item: (
        -sum(int(t.timestamp()) in item[1] and not item[1][int(t.timestamp())].get("conflict")
             for t in targets.values()), item[0]))
    (key, rows) = choices[0] if choices else ((symbol, None, None), {})
    before = rows.get(stamp)
    conflict = not choices and any(k[0] == symbol and r.get(stamp, {}).get("conflict")
                                   for k, r in indexed.items())
    result = {"symbol": symbol, "series_id": key[1], "price_basis": key[2],
              "proxy": before.get("proxy") if before else None,
              "proxy_reason": before.get("proxy_reason") if before else None,
              "baseline_at_utc": cpi.iso(released), "baseline": before["close"] if before else None,
              "baseline_ref": cpi.bar_ref(before), "windows": {}}
    for label, target in targets.items():
        after = rows.get(int(target.timestamp()))
        reason = ("WINDOW_NOT_YET_CLOSED" if target > as_of else
                  "CONFLICTING_BASELINE" if conflict else
                  "PRE_RELEASE_ENDPOINT_ABSENT" if before is None else
                  "EXACT_ENDPOINT_ABSENT" if after is None else
                  "CONFLICTING_ENDPOINT" if after.get("conflict") else None)
        move = round((after["close"] / before["close"] - 1) * 100, 8) if reason is None else None
        result["windows"][label] = {"move_pct": move, "endpoint_at_utc": cpi.iso(target),
            "endpoint": after["close"] if reason is None else None,
            "endpoint_ref": cpi.bar_ref(after), "missing_reason": reason}
    return result


def compare_cells(expected, actual, path, result):
    if isinstance(expected, dict) and isinstance(actual, dict):
        for key in sorted(expected.keys() | actual.keys()):
            compare_cells(expected.get(key), actual.get(key), path + "/" + key, result)
    elif isinstance(expected, list) and isinstance(actual, list) and len(expected) == len(actual):
        for i, (left, right) in enumerate(zip(expected, actual)):
            compare_cells(left, right, path + "/" + str(i), result)
    else:
        result["checked_cells"] += 1
        if expected != actual:
            # Public evidence identifies a failing cell without copying raw prices.
            result["mismatches"].append({"cell": path,
                "recomputed_sha256": digest(json.dumps(expected, sort_keys=True)),
                "exported_sha256": digest(json.dumps(actual, sort_keys=True))})


def surprise_cells(rows):
    """Check public cells and their input identity, without package-only metadata."""
    fields = ("measure", "source", "difference_pp", "normal_spreads", "scale",
              "missing_reason", "scale_missing_reason", "bucket", "knowledge_basis")
    inputs = ("source", "source_url", "known_at_utc", "raw_sha256", "value")
    return [{**{k: row.get(k) for k in fields}, "consensus":
             {k: row["consensus"].get(k) for k in inputs} if row.get("consensus") else None}
            for row in rows]


def join_capture_periods(rows):
    """Reuse CC-068's exact-date/measure join to its explicit source month."""
    explicit = {}
    for row in rows:
        if row.get("source") == "investing" and row.get("reference_period"):
            explicit.setdefault((row.get("measure_id"), row.get("release_date")), set()).add(row["reference_period"])
    for row in rows:
        periods = explicit.get((row.get("measure_id"), row.get("release_date")), set())
        if row.get("reference_period") is None and len(periods) == 1:
            row["reference_period"] = next(iter(periods))
    return rows


def verify_article(article, export):
    binding = article.get("cpi_reaction_page") or {}
    sha = hashlib.sha256(export).hexdigest()
    if binding.get("export_bytes_sha256") != sha:
        raise ValueError("CPI_VERIFICATION_ARTICLE_EXPORT_MISMATCH")
    validate_bound_tables(article)
    record = json.loads(export)["reports"][0]
    body = next(s["body_markdown"]["value"] for s in record["sections"]
                if s["section_id"] == "reaction-tables")
    expected = [digest(reader_names(t, final_copy=True)) for t in tables(body)]
    if binding.get("table_sha256") != expected:
        raise ValueError("CPI_VERIFICATION_ARTICLE_TABLE_MISMATCH")
    return expected


def verify(data_root, code_root, config_path, article_path, seed=425):
    root, code_root = Path(data_root), Path(code_root)
    sys.path.insert(0, str(code_root))
    cpi = importlib.import_module("tools.product.cpi_reaction_history_v1")
    inputs = importlib.import_module("tools.product.cpi_reaction_inputs_v1")
    config = json.loads(Path(config_path).read_bytes())
    libraries = cpi.owners(Path(config["owner_code_root"]))
    internal = json.loads((root / "data.json").read_bytes())
    public_raw, export_raw = (root / "publisher.json").read_bytes(), (root / "desk-export.json").read_bytes()
    public, export = json.loads(public_raw), json.loads(export_raw)
    article = json.loads(Path(article_path).read_bytes())
    if "article" in article:
        article = article["article"]
    source_hash = export["sources"][0]["raw_sha256"]
    if hashlib.sha256(public_raw).hexdigest() != source_hash:
        raise ValueError("CPI_VERIFICATION_PUBLIC_FILE_NOT_BOUND")
    if cpi.public_view(internal) != public:
        raise ValueError("CPI_VERIFICATION_INTERNAL_PUBLIC_MISMATCH")
    expected_body = cpi.markdown(public)
    exported_body = export["reports"][0]["sections"][0]["body_markdown"]["value"]
    if expected_body != exported_body:
        raise ValueError("CPI_VERIFICATION_PUBLIC_TABLE_MISMATCH")
    article_tables = verify_article(article, export_raw)
    selected = sample_releases(internal["events"], seed)
    as_of = cpi.utc(internal["as_of_utc"])
    result = {"item": "CC-425", "state": "CHECKING", "seed": seed,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_as_of_utc": internal["as_of_utc"], "selected_releases": selected,
        "latest_release_covered": internal["events"][-1]["release_utc"],
        "export_sha256": hashlib.sha256(export_raw).hexdigest(),
        "public_file_sha256": source_hash, "article_table_sha256": article_tables,
        "article_file_sha256": hashlib.sha256(Path(article_path).read_bytes()).hexdigest(),
        "consumer": "qualified article -> validate_bound_tables -> exact bound export",
        "checked_cells": 0, "reaction_cells": len(selected) * 6 * 4, "mismatches": [],
        "store_open_mode": "read-only", "public_write_performed": False,
        "network_calls": 0, "source_inputs": []}
    manifest = internal["inputs"]["files"]

    def bound_read(spec, *, rolling_history=False):
        raw = Path(spec["path"]).read_bytes()
        observed = hashlib.sha256(raw).hexdigest()
        if observed != spec["sha256"] and not rolling_history:
            raise ValueError("CPI_VERIFICATION_BOUND_INPUT_CHANGED:" + spec["path"])
        result["source_inputs"].append({"path": spec["path"], "sha256": observed,
            "original_sha256": spec["sha256"], "rolling_history": rolling_history})
        return raw

    first = next(f for f in manifest if f["path"] == config["first_prints_path"])
    archive = [json.loads(line) for line in bound_read(first).splitlines() if line]
    history = {}
    for spec in manifest:
        if Path(spec["path"]).name in {"consensus.json", "package.json"}:
            # The rolling package may gain later rows. Compare the actual
            # as-of surprise cells below; an unrelated refresh is no refusal.
            for row in json.loads(bound_read(spec, rolling_history=Path(spec["path"]).name == "package.json")).get("history", []):
                history[cpi.digest(row)] = row
    # A refresh overwrites the rolling package, but its exact source captures
    # survive. Recover the original as-of records from those files; never use
    # the producer's computed surprise as an independent input.
    capture_root = Path(config["consensus_package"]).parent
    capture_paths = {str((capture_root / row["consensus"]["raw_path"]).parent / "capture.json")
                     for event in internal["events"] for row in event["surprises"]
                     if row.get("consensus") and str(row["consensus"].get("raw_path", "")).startswith("captures/")}
    capture_rows, checked_raw = [], set()
    for path in sorted(capture_paths):
        capture = json.loads(Path(path).read_bytes())
        for row in capture.get("records", []):
            raw_path = capture_root / row["raw_path"]
            if (str(raw_path), row["raw_sha256"]) not in checked_raw:
                if hashlib.sha256(raw_path.read_bytes()).hexdigest() != row["raw_sha256"]:
                    raise ValueError("CPI_VERIFICATION_CAPTURE_HASH_MISMATCH:" + str(raw_path))
                checked_raw.add((str(raw_path), row["raw_sha256"]))
            capture_rows.append(row)
        result["source_inputs"].append({"path": path,
            "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(), "as_of_capture_recovery": True})
    for row in join_capture_periods(capture_rows):
        history[cpi.digest(row)] = row
    # Pin each forecast to the source observation chosen by this edition.
    # Other surviving captures can include newer observations which were not
    # in that package. Their existence does not change the bound page's clock.
    pinned = {(event["release_utc"][:10], cpi.MEASURES[row["measure"]], row["source"]):
              row.get("consensus") for event in internal["events"] for row in event["surprises"]}
    bound_history = []
    for row in history.values():
        key = (row.get("release_date"), row.get("measure_id"), row.get("source"))
        if key in pinned:
            chosen = pinned[key]
            if not chosen or any(row.get(k) != chosen.get(k) for k in ("known_at_utc", "raw_sha256")):
                continue
        bound_history.append(row)
    surprises = cpi.surprises(archive, bound_history, as_of, libraries["betas"].spread)
    loaded, gaps = [], []
    bars = inputs.historical_bars(config, libraries, selected, as_of, loaded, gaps)
    needed = {int(t.timestamp()) for release in selected for t in
              [cpi.utc(release), *cpi.endpoints(cpi.utc(release)).values()]}
    roots = {Path(f["path"]).parent.parent.parent for f in manifest
             if Path(f["path"]).name == "capture.json"}
    for path in sorted(roots):
        bars += inputs.dukascopy_bars(path, libraries, as_of, loaded, gaps, needed)
    bars += inputs.held_m15_bars(config["completed_bar_store"], as_of, gaps, needed)
    expected_hashes = {f["path"]: f["sha256"] for f in manifest}
    for spec in loaded:
        if spec["path"] in expected_hashes and spec["sha256"] != expected_hashes[spec["path"]]:
            raise ValueError("CPI_VERIFICATION_BOUND_INPUT_CHANGED:" + spec["path"])
    if gaps:
        raise ValueError("CPI_VERIFICATION_INPUT_ERROR:" + json.dumps(gaps[0], sort_keys=True))
    result["source_inputs"].extend(loaded)
    indexed = cpi.index_bars(bars, as_of)
    for event in internal["events"]:
        release = event["release_utc"]
        if release not in selected:
            continue
        prefix = "/events/" + event["event_id"]
        actuals = [r for measure in cpi.MEASURES for r in archive
                   if r.get("series") == measure and r["release_datetime_utc"] == release]
        compare_cells(actuals, event["actuals"], prefix + "/actuals", result)
        recomputed_surprises = [row for measure in cpi.MEASURES
                               for row in surprises.get((release, measure), [])]
        compare_cells(surprise_cells(recomputed_surprises), surprise_cells(event["surprises"]),
                      prefix + "/surprises", result)
        compare_cells(actuals[0]["reference_period"], event["reference_period"], prefix + "/reference_period", result)
        markets = [recompute_market(symbol, indexed, cpi.utc(release), as_of, cpi) for symbol in cpi.MARKETS]
        compare_cells(markets, event["markets"], prefix + "/markets", result)
    compare_cells(cpi.summarize(internal["events"]), internal["summary"], "/summary", result)
    result["decoded_bars"] = len(bars)
    result["state"] = "PASS" if not result["mismatches"] else "FAIL"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ["data-root", "code-root", "config", "article", "out"]:
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--seed", type=int, default=425)
    args = parser.parse_args()
    try:
        result = verify(args.data_root, args.code_root, args.config, args.article, args.seed)
    except (OSError, ValueError, KeyError) as exc:
        result = {"item": "CC-425", "state": "FAIL", "cause": str(exc),
                  "observed_at_utc": datetime.now(timezone.utc).isoformat()}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items()
                     if k in {"state", "cause", "checked_cells", "reaction_cells", "selected_releases"}} |
                     {"mismatch_count": len(result.get("mismatches", [])),
                      "first_mismatch": next(iter(result.get("mismatches", [])), None)}))
    return 0 if result["state"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
