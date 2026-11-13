# What the Claude Code inspection established

Artifact: official npm `@anthropic-ai/claude-code-linux-x64@2.1.323`. SHA-256 `604d29a6869409106b6a1110bdadcc8b72e8654a5a865d23258f938a696e348e`. REA: 6.9.0, [commit a8527d43](https://github.com/morluto/rea/tree/a8527d43b8439476f5c9d1497315dfe7dd5e1f38).

The standard REA Bun expansion path refused repeated accounting of overlapping bytecode ranges. A bounded contents-only adapter using the unmodified REA decoder recovered 3,237 embedded source/assets totaling 63,760,938 bytes. A second extraction reproduced every file hash. No bytecode decompilation, inference call or hosted-weight extraction occurred.

## Auto mode

The client contains policy construction, context filtering, model routing, fast and reasoning requests, Boolean/severity parsing, retry logic and outer permission handling. In the inspected path, the call chain ends at the configured provider's `beta.messages.create`, not a local neural runtime. Model routing is affected by server configuration, user overrides and provider availability. Current official docs describe Sonnet 5 by default for client-requested review; the historical March 2026 engineering article described Sonnet 4.6.

The fast and escalated checks in this client use the selected hosted model. They are not evidence of a tiny first-stage weight file. The build supports Boolean block tags and numeric severity outputs. Its fallback Sonnet 5 thresholds are 25 and 35, dynamically overridable and **not probabilities**. They cannot be transferred to a different model as calibrated confidence thresholds.

Classifier helpers block on API/parsing failures. The outer runtime has specific prompt, compaction, handoff and agent-spawn handling; claiming every runtime failure always blocks every action would overstate the evidence. Current server-integrated safeguards are another path whose implementation is not recovered from the client.

`claude auto-mode defaults` is a documented policy export. The inspected version yielded 16 allow, 72 soft-deny, 1 hard-deny and 21 environment entries. These are prose policies, not model weights. No full proprietary policy or extracted implementation is included in this public repository.

## ToolSearch

The local `qNt` ranker in `chunk-187gn6d6.js` performs direct selection, exact/MCP-prefix paths, required-term filtering and weighted name, search-hint and description matching. Its schema/wrapper lives in `chunk-579w43z0.js`. Our independent scorer recreates this limited deterministic behavior; no learned search model was needed.

The public hosted regex/BM25 tools are separate. Public client-side `tool_reference` results allow an application to implement its own retrieval. Retrieval relevance never grants execution permission.

## Advisor

The client declares a hosted `advisor_20260301` tool with the `advisor-tool-2026-03-01` beta and selected advisor model. Its local orchestration does not contain the hosted advisor's model weights or complete private server prompt. The public API can be used directly where supported. Optional advice and its error behavior are distinct from authorization.

## Useful references

- [REA Bun analysis](https://github.com/morluto/rea/blob/a8527d43b8439476f5c9d1497315dfe7dd5e1f38/docs/bun-standalone.md)
- [Claude auto-mode configuration](https://code.claude.com/docs/en/auto-mode-config)
- [Claude permission modes](https://code.claude.com/docs/en/permission-modes)
- [Historical auto-mode architecture](https://www.anthropic.com/engineering/claude-code-auto-mode)
- [Tool-search API](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool)
- [Advisor API](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool)

Static inspection supports architecture and request-contract findings. It does not establish behavior under every live account configuration, model equivalence, latency or safety accuracy.

The expanded [context and memory map](context/README.md) documents transcript projection, persistent memory, compaction, request assembly, ToolSearch/advisor boundaries, and exact evidence locations. An independent packet builder makes the supported context transformations executable and auditable.
