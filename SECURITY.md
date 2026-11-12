# Security status

This is research software, not a production security boundary. It never executes proposed tools. Callers must enforce actual permissions, authenticate policy/context, resolve real effects, prevent stale approval reuse and retain process/filesystem/network isolation.

Default shadow mode returns review requests. Enabling automatic approval is an explicit host decision after evaluation. Missing context, unknown tools, API errors and malformed model outputs must not be interpreted as approval.

The passive Claude hook collector is not an enforcement hook and does not fail the tool call when logging fails. Its redaction is incomplete by design; keep observations private and inspect them before sharing.

For a vulnerability report, use GitHub's private vulnerability reporting if enabled; otherwise open an issue containing only a non-sensitive reproducer and request a private reporting channel. Do not post secrets, real transcripts or destructive payloads targeting live systems.
