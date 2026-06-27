# Operator Source Evidence Submission Guide

> [!IMPORTANT]
> **NO-PUBLICATION WARNING**: This is an operator staging document. It must not be published or sent to any live Discord channel.

## Purpose
This lane provides operator guidelines for submitting verified underlying evidence to unblock facts or claims.

## Accepted Evidence Shapes
- **local_doc_path**: Local PDF/Word paths such as `docs/evidence/jim_verified_audit_notes.pdf`.
- **repo_file_path**: Path of verified repo markdown/JSON documents.
- **screenshot_path**: Path of verified operator screenshots.
- **official_source_url_to_be_reviewed_later**: URL pointers to official filings or reports.
- **operator_note**: Custom text statements detailing manual audits.

## Unsafe / Forbidden Input Examples (Will Be Rejected)
- Webhook endpoints (`discord.com/api/webhooks/...`)
- Security/auth strings containing `token`, `cookie`, `secret`, `bearer`, or `authorization`
- System configuration paths pointing to `.env` files

## Factual Validation Constraint
- This task validates slot completeness and safe reference formatting only. It does not verify factual truth itself.
- Do not invent sources, citations, CPC figures, or market statistics.
