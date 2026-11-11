"""CC-427: an offline, risk-normalised FTMO 2-Step audit from held records.

Reads captured files only. Never imports a broker client, writes to Main, or sends
a post. Original account values stop at the private adapter. The newsroom receives
only aggregate model results and source hashes.
"""
from __future__ import annotations

from collections import defaultdict
from itertools import groupby
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from .capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of

SCHEMA = "contentops.prop_challenge.v1"
AUTHORSHIP = "CAPITAL_CHRONICLE_PROP_CHALLENGE_AUDIT"
RULES_PATH = Path(__file__).resolve().parents[1] / "config/ftmo_two_step_rules_v1.json"
PRAGUE = ZoneInfo("Europe/Prague")
ET = ZoneInfo("America/New_York")
ZERO = Decimal(0)


def number(value):
    if value is None or isinstance(value, bool):
        raise ValueError("PROP_NUMBER_ABSENT")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("PROP_NUMBER_INVALID") from exc
    if not result.is_finite():
        raise ValueError("PROP_NUMBER_INVALID")
    return result


def instant(value):
    result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("PROP_TIMEZONE_REQUIRED")
    return result.astimezone(timezone.utc)


def month_start(month):
    value = datetime.strptime(month, "%Y-%m")
    return value.replace(tzinfo=ET).astimezone(timezone.utc)


def position_reference(ticket):
    # Existing Main bridge identity, mt5_demo_outcome_bridge_v1._reference.
    value = hashlib.sha256(f"capital-chronicle-phase-e:position:{ticket}".encode()).hexdigest()
    return "position_" + value[:32]


def load_rules(path=RULES_PATH):
    rules = json.loads(Path(path).read_bytes())
    return validate_rules(rules)


def validate_rules(rules):
    if (rules.get("schema_version") != "contentops.prop_rules.v1"
            or rules.get("program") != "FTMO_CFD_2_STEP"
            or rules.get("day_timezone") != "Europe/Prague"):
        raise ValueError("PROP_RULE_PROFILE_INVALID")
    for source in rules["sources"].values():
        blob = (RULES_PATH.parent.parent / source["capture_path"]).read_bytes()
        if hashlib.sha256(blob).hexdigest() != source["capture_sha256"]:
            raise ValueError("PROP_RULE_SOURCE_CHANGED")
    return rules


def held_dataset(economic_path, journal_dir, *, month, cutoff_utc):
    """Exact broker position references join frozen risk; no time/price matching.

    The one explicitly labelled ops_test_ round trip is reported as excluded.
    Unattributed genuine records cause an error rather than a flattering sample.
    Deposits/credits are not model trading profits. Costs retain their deal clock.
    """
    raw = Path(economic_path).read_bytes()
    economic = json.loads(raw)
    statement = economic["statement"]
    observation = statement["source_observation"]
    cutoff, start = instant(cutoff_utc), month_start(month)
    if not start <= cutoff or cutoff.astimezone(ET).strftime("%Y-%m") != month:
        raise ValueError("PROP_CUTOFF_OUTSIDE_MONTH")
    known = instant(statement["known_at_utc"])
    if known > cutoff or instant(observation["coverage_to_utc"]) > cutoff:
        raise ValueError("PROP_SOURCE_AFTER_CUTOFF")
    if (not statement["complete_since_baseline"]
            or instant(observation["coverage_from_utc"]) > start):
        raise ValueError("PROP_DEAL_HISTORY_INCOMPLETE")
    if observation["environment"] != "DEMO":
        raise ValueError("PROP_DEMO_RECORDS_REQUIRED")
    if not (statement["account_binding"] == observation["account_binding"]
            == observation["reconciliation"]["account_binding"]):
        raise ValueError("PROP_ACCOUNT_BINDING_CHANGED")
    manifests = [{"path": str(Path(economic_path).resolve()),
                  "sha256": hashlib.sha256(raw).hexdigest(), "role": "held_statement"}]
    journals = defaultdict(list)
    for path in sorted(Path(journal_dir).glob("*.json")):
        blob = path.read_bytes()
        journal = json.loads(blob)
        if journal.get("position_ticket") is not None:
            journals[position_reference(journal["position_ticket"])].append((journal, path, blob))
    groups = defaultdict(list)
    ignored_cash = 0
    seen_facts = set()
    for row in statement["broker_records"].values():
        if row["fact_hash"] in seen_facts:
            raise ValueError("PROP_DUPLICATE_DEAL")
        seen_facts.add(row["fact_hash"])
        fact = row["fact"]
        at = instant(fact["effective_at_utc"])
        if at > cutoff:
            continue
        if fact["deal_type"] not in (0, 1):
            ignored_cash += int(at >= start)
            continue
        # Bridge account_fingerprint_hash identifies a particular observation,
        # not the stable account. Use the producer's stable statement binding
        # and the exact position/risk identity, checked below.
        groups[fact["position_reference"]].append(row)
    trades, probes = [], []
    for ref, rows in sorted(groups.items()):
        rows.sort(key=lambda row: (instant(row["fact"]["effective_at_utc"]), row["fact_hash"]))
        entries = [r for r in rows if r["fact"]["deal_entry"] == 0]
        exits = [r for r in rows if r["fact"]["deal_entry"] == 1]
        if len(entries) != 1 or len(entries) + len(exits) != len(rows):
            raise ValueError("PROP_UNSUPPORTED_ENTRY_OR_REVERSAL")
        opened = instant(entries[0]["fact"]["effective_at_utc"])
        closed_volume = sum((number(r["fact"]["volume"]["executed"]) for r in exits), ZERO)
        entry_volume = number(entries[0]["fact"]["volume"]["executed"])
        if entry_volume <= ZERO or closed_volume > entry_volume:
            raise ValueError("PROP_DEAL_VOLUME_CONFLICT")
        closed = closed_volume == entry_volume
        last = instant(rows[-1]["fact"]["effective_at_utc"])
        if opened < start and closed and last < start:
            continue
        if (entries[0]["fact"].get("normalized_comment") or "").startswith("ops_test_"):
            probes.append({"position_reference": ref, "fact_hashes": [r["fact_hash"] for r in rows]})
            continue
        if opened < start:
            raise ValueError("PROP_MONTH_START_CARRY_IN_REQUIRES_OPENING_BOOK")
        matches = journals.get(ref, [])
        if not matches:
            raise ValueError("PROP_INITIAL_RISK_RECORD_ABSENT:" + ref)
        identities = [j[0]["intent_identity"] for j in matches]
        risks = {number(i["initial_risk_cash"]) for i in identities}
        if len(risks) != 1:
            raise ValueError("PROP_INITIAL_RISK_CONFLICT")
        risk = next(iter(risks))
        if risk <= ZERO:
            raise ValueError("PROP_INITIAL_RISK_INVALID")
        for identity in identities:
            if (identity["stable_account_identity_hash"] != observation["account_binding"]
                    or identity["initial_risk_currency"] != observation["currency"]
                    or instant(identity["risk_frozen_at_utc"]) > opened):
                raise ValueError("PROP_RISK_IDENTITY_CURRENCY_OR_CLOCK_CONFLICT")
        journal, path, blob = matches[0]
        manifests.append({"path": str(path.resolve()), "sha256": hashlib.sha256(blob).hexdigest(),
                          "role": "frozen_initial_risk", "position_reference": ref})
        events = []
        for row in rows:
            f = row["fact"]
            cash = sum((number(f[k]) for k in ("profit", "commission", "swap", "fee")), ZERO)
            events.append({"at_utc": f["effective_at_utc"], "net_r": str(cash / risk),
                           "entry": f["deal_entry"] == 0, "fact_hash": row["fact_hash"]})
        trades.append({"trade_id": sha256_of(ref)[:16], "opened_at_utc": entries[0]["fact"]["effective_at_utc"],
                       "closed_at_utc": rows[-1]["fact"]["effective_at_utc"] if closed else None,
                       "events": events, "position_reference": ref,
                       "risk_record_sha256": hashlib.sha256(blob).hexdigest()})
    if not trades:
        raise ValueError("PROP_NO_RECORDED_DESK_TRADES")
    return {"schema_version": "contentops.prop_private_dataset.v1", "month": month,
            "cutoff_utc": cutoff_utc, "source_known_at_utc": statement["known_at_utc"],
            "trades": trades, "excluded_operations_tests": probes,
            "excluded_cash_record_count": ignored_cash, "source_manifest": manifests,
            "equity_path_complete": False,
            "equity_path_cause": "NORMALISED_INTRADAY_EQUITY_PATH_ABSENT",
            "held_account_equity_gap_count": len(statement["unobserved_intervals"]),
            "held_account_equity_gap_reasons": sorted({g["reason"] for g in statement["unobserved_intervals"]})}


def evaluate(dataset, rules, *, phase="challenge"):
    """Full period, one fixed 0.5% starting-capital risk unit per original plan.

    A single observed breach proves failure. Sampled non-breaches cannot prove
    an intraday equity pass. Prague midnight uses *balance*, never floating P/L.
    There is no challenge time limit, so NOT_MET is dated, not a terminal failure.
    """
    if phase not in ("challenge", "verification"):
        raise ValueError("PROP_EVALUATION_PHASE_REQUIRED")
    profile = rules["phases"][phase]
    scale = number(rules["model"]["risk_pct_initial_capital"])
    if scale != Decimal("0.5"):
        raise ValueError("PROP_J1_RISK_REQUIRED")
    cutoff = instant(dataset["cutoff_utc"])
    trades = dataset["trades"]
    ids = [t["trade_id"] for t in trades]
    if len(set(ids)) != len(ids) or not ids:
        raise ValueError("PROP_TRADE_ID_CONFLICT")
    ledger = []
    for trade in trades:
        opening = instant(trade["opened_at_utc"])
        closing = instant(trade["closed_at_utc"]) if trade["closed_at_utc"] else None
        if opening > cutoff or (closing and (closing > cutoff or closing < opening)):
            raise ValueError("PROP_TRADE_CLOCK_INVALID")
        for index, event in enumerate(trade["events"]):
            at = instant(event["at_utc"])
            if at < opening or at > cutoff or (closing and at > closing):
                raise ValueError("PROP_EVENT_CLOCK_INVALID")
            ledger.append((at, trade["trade_id"], index, number(event["net_r"]) * scale))
    ledger.sort()
    balance = Decimal(100)
    checkpoints = []
    start_balance_by_day = {}
    for at, simultaneous in groupby(ledger, key=lambda row: row[0]):
        day = at.astimezone(PRAGUE).date().isoformat()
        start_balance_by_day.setdefault(day, balance)
        balance += sum((row[3] for row in simultaneous), ZERO)
        active = [t for t in trades if instant(t["opened_at_utc"]) <= at
                  and (not t["closed_at_utc"] or instant(t["closed_at_utc"]) > at)]
        # Ledger points are exact equity only when every position is flat.
        if not active:
            checkpoints.append({"at_utc": at.isoformat(), "balance": balance, "flat": True,
                                "day_start_balance": start_balance_by_day[day]})
    # An optional normalised complete equity tape is already net of accrued
    # costs. It is distinct from raw account equity, which is never rescaled.
    for point in dataset.get("equity_points", []):
        at = instant(point["at_utc"])
        if not month_start(dataset["month"]) <= at <= cutoff:
            raise ValueError("PROP_EQUITY_CLOCK_INVALID")
        midnight = datetime.combine(at.astimezone(PRAGUE).date(), datetime.min.time(), PRAGUE)
        day_balance = Decimal(100) + sum((d for t, _, _, d in ledger if t < midnight), ZERO)
        checkpoints.append({"at_utc": point["at_utc"], "balance": number(point["equity_index"]), "flat": False,
                            "day_start_balance": day_balance})
    max_daily = max((p["day_start_balance"] - p["balance"] for p in checkpoints), default=ZERO)
    max_overall = max((Decimal(100) - p["balance"] for p in checkpoints), default=ZERO)
    flat_target = any(p["balance"] >= Decimal(100) + number(profile["profit_target_pct"])
                      for p in checkpoints if p["flat"])
    days = sorted({instant(t["opened_at_utc"]).astimezone(PRAGUE).date().isoformat() for t in trades})
    complete = dataset.get("equity_path_complete") is True and bool(dataset.get("equity_points"))
    def loss_verdict(measured, limit):
        return "FAIL" if measured > number(limit) else "PASS" if complete else "UNKNOWN"
    rows = [
        {"rule": "profit_target", "verdict": "PASS" if flat_target else "NOT_MET",
         "required_pct": profile["profit_target_pct"], "source": "profit_target",
         "reason": "Target must be reached with every position closed; no time limit."},
        {"rule": "maximum_daily_loss", "verdict": loss_verdict(max_daily, profile["maximum_daily_loss_pct"]),
         "limit_pct": profile["maximum_daily_loss_pct"], "source": "daily_loss",
         "reason": "Prague midnight balance less the fixed limit; floating P/L and costs count."},
        {"rule": "maximum_loss", "verdict": loss_verdict(max_overall, profile["maximum_loss_pct"]),
         "limit_pct": profile["maximum_loss_pct"], "source": "maximum_loss",
         "reason": "Equity must not fall below the fixed initial-capital floor."},
        {"rule": "minimum_trading_days", "verdict": "PASS" if len(days) >= profile["minimum_trading_days"] else "NOT_MET",
         "required_days": profile["minimum_trading_days"], "observed_days": len(days), "source": "trading_days",
         "reason": "Count days with an opening execution in Europe/Prague."},
        {"rule": "news_window", "verdict": "NOT_APPLICABLE", "source": "news",
         "reason": "Challenge and Verification are exempt from the two-minute restriction; forbidden practices still apply."},
        {"rule": "weekend_holding", "verdict": "NOT_APPLICABLE", "source": "weekend",
         "reason": "Challenge and Verification are exempt from the long-market-break restriction; forbidden practices still apply."}]
    closed_count = sum(t["closed_at_utc"] is not None for t in trades)
    return {"schema_version": SCHEMA, "month": dataset["month"], "cutoff_utc": dataset["cutoff_utc"],
            "source_known_at_utc": dataset["source_known_at_utc"], "program": rules["program"], "phase": phase,
            "rule_version": rules["version"], "rules_sha256": sha256_of(rules),
            "private_dataset_sha256": sha256_of(dataset), "model": dict(rules["model"]),
            "trade_count": len(trades), "closed_trade_count": closed_count,
            "open_trade_count": len(trades) - closed_count, "trading_days": len(days),
            "booked_model_change_pct": str(balance - Decimal(100)),
            "excluded_operations_test_count": len(dataset["excluded_operations_tests"]),
            "excluded_cash_record_count": dataset["excluded_cash_record_count"],
            "equity_path_complete": complete, "equity_path_cause": dataset.get("equity_path_cause"),
            "observed_flat_checkpoint_count": sum(p["flat"] for p in checkpoints),
            "rules": rows,
            "overall": "FAIL" if any(r["verdict"] == "FAIL" for r in rows)
                       else "NOT_PASSED_AS_OF_CUTOFF" if any(r["verdict"] == "NOT_MET" for r in rows)
                       else "UNVERIFIED" if any(r["verdict"] == "UNKNOWN" for r in rows) else "PASS"}


def source_document(report, rules):
    """A public aggregate source, never a private statement in a writer prompt."""
    fields = {"schema_version", "month", "cutoff_utc", "source_known_at_utc", "program", "phase",
        "rule_version", "rules_sha256", "private_dataset_sha256", "model", "trade_count", "closed_trade_count",
        "open_trade_count", "trading_days", "booked_model_change_pct", "excluded_operations_test_count",
        "excluded_cash_record_count", "equity_path_complete", "equity_path_cause", "observed_flat_checkpoint_count",
        "rules", "overall"}
    if set(report) != fields or report["model"] != rules["model"]:
        raise ValueError("PROP_PUBLIC_AGGREGATE_FIELDS_REQUIRED")
    text = (f"FTMO 2-Step {report['phase']}, {report['month']}, as of {report['cutoff_utc']}.\n"
            f"Model risk: {report['model']['risk_pct_initial_capital']}% of starting model capital per frozen original risk unit.\n"
            f"Desk positions: {report['trade_count']}; closed: {report['closed_trade_count']}; open: {report['open_trade_count']}.\n"
            f"Opening days (Prague): {report['trading_days']}. Excluded labelled operations tests: {report['excluded_operations_test_count']}.\n"
            f"Booked model change: {number(report['booked_model_change_pct']):.2f}%; excludes unrealised P/L, so it is not an equity return.\n"
            f"Overall: {report['overall']}.\n")
    for row in report["rules"]:
        threshold = row.get("required_pct", row.get("limit_pct", row.get("required_days")))
        unit = " days" if "required_days" in row else "%"
        detail = f" Requirement: {threshold}{unit}." if threshold is not None else ""
        text += f"{row['rule']}: {row['verdict']}.{detail} {row['reason']} Source: {rules['sources'][row['source']]['url']}\n"
    text += ("Loss-limit passes are unverified because the normalised intraday equity path is absent. "
             "This is a model replay of recorded executions, not an FTMO account result, certification or a strategy to copy. "
             "FTMO's forbidden-practices rules remain separate; this audit does not certify compliance with every contractual term.")
    digest = hashlib.sha256(text.encode()).hexdigest()
    binding = {"report": report, "rules": rules, "rules_sha256": sha256_of(rules), "text_sha256": digest}
    return {"document_id": "prop-challenge-" + sha256_of(report), "source_id": "SOURCE_1",
            "url": "urn:cc-public-report:prop-challenge:" + sha256_of(binding),
            "source_url": "urn:cc-public-report:prop-challenge:" + sha256_of(binding),
            "publisher": "Capital Chronicle", "published_at_utc": report["source_known_at_utc"],
            "published_at_source": "HELD_SOURCE_CAPTURE_NOT_PUBLIC_PUBLICATION",
            "data_cutoff_utc": report["cutoff_utc"],
            "canonical_content_text": text, "canonical_content_sha256": digest,
            "raw_sha256": sha256_of(report), "content_truncated": False,
            "public_claim_allowed": True, "source_authority_class": "capital_chronicle_computed_model",
            "prop_challenge_binding": binding,
            "source_reuse_constraints": {"public_expression_reuse_allowed": True,
                "scope": "CC427_AGGREGATE_MODEL_AUDIT_JIM_DECISIONS_40_72B_111"}}


def verified_source_metadata(document):
    binding = document.get("prop_challenge_binding")
    if not binding:
        return None
    if (document.get("source_authority_class") != "capital_chronicle_computed_model"
            or document.get("source_url") != "urn:cc-public-report:prop-challenge:" + sha256_of(binding)
            or document.get("canonical_content_sha256") != binding["text_sha256"]
            or hashlib.sha256(document.get("canonical_content_text", "").encode()).hexdigest() != binding["text_sha256"]):
        raise ValueError("PROP_PUBLIC_SOURCE_CHANGED")
    frozen_rules = validate_rules(binding["rules"])
    if (binding["rules_sha256"] != sha256_of(frozen_rules)
            or binding["report"]["rules_sha256"] != sha256_of(frozen_rules)):
        raise ValueError("PROP_FROZEN_RULES_CHANGED")
    expected = source_document(binding["report"], frozen_rules)
    if expected != document:
        raise ValueError("PROP_PUBLIC_SOURCE_CHANGED")
    return binding


def retained_record(spec, document):
    """Project this computed output into the existing retained-source library."""
    from .event_article_guard_v1 import check_publication_copy
    verified_source_metadata(document)
    if (spec.get("authorship_class") != AUTHORSHIP or spec.get("authority_ref") != "BACKLOG_CC427_JIM_DECISION_111"
            or spec.get("document_sha256") != sha256_of(document)
            or instant(spec["revision_at_utc"]) < instant(document["data_cutoff_utc"])):
        raise ValueError("PROP_RETAINED_SOURCE_BINDING_INVALID")
    title = spec["headline_text"]
    text = document["canonical_content_text"]
    check_publication_copy({"text": text, "title": title}, require_notice=False)
    permission = {**document["source_reuse_constraints"], "provider_safe": True,
                  "MODEL_INPUT_ALLOWED": True, "LLM_INPUT_ALLOWED": True, "INTERNAL_ANALYSIS_ALLOWED": True,
                  "permitted_consumers": ["internal_research", "narrative_context"],
                  "source_capture_sha256": spec["document_sha256"]}
    known = document["published_at_utc"]
    return {"headline_id": spec["headline_id"], "headline_text": title,
            "text_sha256": hashlib.sha256(title.encode()).hexdigest(),
            "source_identity": "Capital Chronicle model audit", "source_account": "Capital Chronicle",
            "source_platform": AUTHORSHIP, "source_url": document["source_url"],
            "source_timestamp_utc": known, "headline_timestamp": known,
            "known_at_utc": known, "retrieval_time_utc": known, "revision_at_utc": spec["revision_at_utc"],
            "revision_clock_basis": "MODEL_AUDIT_PREPARATION_NOT_NEW_DATA_CAPTURE",
            "rights_state": "CAPITAL_CHRONICLE_OWN_AGGREGATE_MODEL_OUTPUT",
            "source_permissions": permission, "permitted_source_text": text,
            "document": document, "research_metadata": {"period_relation": "MONTH_TO_DATE_REPLAY",
                "data_cutoff_utc": document["data_cutoff_utc"],
                "public_report_sha256": document["raw_sha256"]}}
