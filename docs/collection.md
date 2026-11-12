# Collecting useful data without inventing classifier labels

## What current Claude Code hooks expose

Checked against the official hooks documentation on 2026-11-12 and the prior static inspection of 2.1.323. Hooks and server behavior can change; record your exact CLI version.

| Event | What it establishes | What it does not establish |
| --- | --- | --- |
| PreToolUse | A candidate call and correlation ID | Whether the auto classifier evaluated or approved it |
| PostToolUse | The tool returned a result | Whether approval came from classifier, allow rule, built-in fast path, user or another hook |
| PostToolUseFailure | Execution failed | A safety denial or an unsafe ground-truth label |
| PermissionDenied | Auto mode denied this call | Always a model verdict: unavailable/unparseable/refused classifier requests also trigger it |
| PermissionRequest | A permission decision is needed | A universal interception point for every classified action |

For `PermissionDenied`, current documentation distinguishes the fixed `Classifier unavailable` reason and a prefix beginning `Auto mode could not evaluate this action` from ordinary rule-based denials. The collector records this distinction as an observation, never as a verified label. A bracketed rule reason is a candidate negative example that still needs version/context review.

There is no supported hook in the inspected contract that supplies the complete classifier input plus every positive and negative verdict without execution. We did not establish a standalone public endpoint for the private auto-mode classifier. Current server-integrated review further limits what local instrumentation can observe.

**Blocking a call in PreToolUse changes the pipeline.** A blanket deny/defer hook can prevent the native permission/classifier stage from being reached. Do not claim that this is a safe offline oracle for the native classifier. Conversely, observing allowed real shell calls may execute them; run experiments only against inert application tools or genuinely isolated synthetic environments. Replacing a real tool with a simulator changes its semantics and may change the classifier's decision.

## Passive collector

Review and adapt `examples/claude-hooks.json` to your installed package's absolute Python path and a private local output directory. Merge the hooks into your own settings; the project never edits Claude settings automatically. Default collection saves event metadata and an argument digest. `--include-input` explicitly opts into storing redacted arguments and denial reasons.

```sh
python -m small_auto_mode.collection --output data/local-observations < event.json
```

It always emits `{}` to hook stdout. It returns no permission decision, no updated arguments and no retry request. It ignores `transcript_path`, cwd and tool output. Each event is saved in a separate file with mode 0600. The collector is not an enforcement hook; logging failures do not change the host's existing permission decision.

Redaction is best effort and cannot recognize every secret, personal datum or sensitive command argument. Files remain local and ignored by git. Review them before sharing. Configure output outside any directory an untrusted executor can modify. Supply `--claude-code-version` explicitly, since the collector does not run the CLI to discover it.

## Constructing reviewed records

Use `examples/record.template.json` as the schema. Fill in authenticated user intent, durable constraints, the actual tool call and trusted environment facts. Include relevant prior context with its provenance in `history`; do not promote retrieved instructions or the assistant's justifications to user authority. Resolve missing context before labeling.

- `allow`: authorized and acceptable under the task policy.
- `ask`: authorization or essential context is insufficient; human review is required.
- `deny`: the action violates policy or a durable user prohibition.

`label.verified` means a reviewer actually confirmed the label and context. `provenance.context_reviewed` must be true. Keep source, reviewer, rights basis, CLI/model version, policy version and evidence references. Automated model predictions are suggestions until this process confirms them. An `ask` call counts as unsafe to auto-approve in evaluation.

Avoid selection bias: denials alone cannot train a useful classifier. Include permitted calls, near misses and pairs where the same command has different authorization. Keep unavailable/error cases outside the semantic label corpus. Negative native observations are neither a complete teacher distribution nor ground truth about what the user intended.

## Using teacher data

Three sources should stay separate:

1. **Human / owned simulation oracle**: the default training source.
2. **Ordinary teacher model**: an explicit classification prompt sent to a permitted model. Even if this is Claude, it is not the native Claude Code auto classifier.
3. **Native auto-classifier evidence**: a verified event with exact version, context and evidence. Public hooks provide only a partial view; do not fabricate missing allows or exact native context.

The dataset tool rejects `hook_observation` and unverified records. By default it accepts only `human`; `--allow-source teacher_model` or `--allow-source claude_auto_classifier` is an explicit opt-in, still requiring documented rights and review. These fields are provenance assertions by the dataset owner, not legal verification by software.

Anthropic's [commercial terms, D.4](https://www.anthropic.com/legal/commercial-terms) restrict access to build competing products, including training competing AI models, except as expressly approved. Its [consumer terms](https://www.anthropic.com/legal/consumer-terms) contain related restrictions. Do not assume owning output or having a paid account settles this intended use. Use owned human labels or an openly licensed/expressly permitted teacher where appropriate; verify applicable terms before constructing a released Claude-derived corpus. No such corpus is included here.

## Sources

- [PermissionDenied hook](https://code.claude.com/docs/en/hooks#permissiondenied)
- [PreToolUse hook](https://code.claude.com/docs/en/hooks#pretooluse)
- [SDK hooks](https://code.claude.com/docs/en/agent-sdk/hooks)
- [SDK permission flow](https://code.claude.com/docs/en/agent-sdk/permissions)
- [Auto-mode configuration](https://code.claude.com/docs/en/auto-mode-config)
