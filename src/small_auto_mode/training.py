"""Optional Transformers training pipeline. No generated-text verdict parsing."""
import argparse
import hashlib
import json
from pathlib import Path
from .dataset import LABELS, input_text, read_records
from .metrics import choose_threshold, fit_temperature, report, softmax

BASE_MODEL = "Qwen/Qwen3-0.6B"
BASE_REVISION = "c1899de289a04d12100db370d81485cdf75e47ca"


def verified_splits(directory):
    directory = Path(directory)
    manifest = json.loads((directory / "manifest.json").read_text())
    splits = {}
    observed = {"session_id": set(), "scenario_family": set(), "content": set()}
    for name in ("train", "calibration", "test"):
        path = directory / (name + ".jsonl")
        if hashlib.sha256(path.read_bytes()).hexdigest() != manifest["splits"][name]["sha256"]:
            raise ValueError("split hash mismatch: " + name)
        rows = read_records(path, manifest["allowed_sources"])
        for key in observed:
            values = {input_text(r) if key == "content" else r[key] for r in rows}
            if observed[key] & values:
                raise ValueError("partition leakage: " + key)
            observed[key].update(values)
        splits[name] = rows
    if {r["label"]["decision"] for r in splits["train"]} != set(LABELS):
        raise ValueError("training requires all classes")
    return splits, manifest


def encode(records, tokenizer, max_length):
    result = []
    for row in records:
        encoded = tokenizer(input_text(row), truncation=False, return_token_type_ids=False)
        if len(encoded["input_ids"]) > max_length:
            raise ValueError(f"{row['id']}: context exceeds token budget; review it, do not silently truncate")
        encoded["labels"] = LABELS.index(row["label"]["decision"])
        result.append(encoded)
    return result


def run_training(model, tokenizer, splits, output, *, epochs=1, batch_size=1,
                 max_length=4096, full_finetune=False, device="cpu", smoke=False):
    import torch
    from transformers import DataCollatorWithPadding
    from torch.utils.data import DataLoader
    count = sum(p.numel() for p in model.parameters())
    if count > 1_000_000_000:
        raise ValueError("base plus classifier head exceeds the 1B parameter cap")
    if epochs < 1 or batch_size < 1 or max_length < 8:
        raise ValueError("invalid training controls")
    output = Path(output)
    if output.exists():
        raise ValueError("output must be a new directory")
    torch.manual_seed(42)
    model.to(device)
    if not full_finetune:
        model.requires_grad_(False)
        model.score.requires_grad_(True)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    collate = DataCollatorWithPadding(tokenizer, return_tensors="pt")
    encoded = {k: encode(v, tokenizer, max_length) for k, v in splits.items()}
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=2e-5 if full_finetune else 1e-3)
    for _ in range(epochs):
        model.train()
        for batch in DataLoader(encoded["train"], batch_size=batch_size, shuffle=True, collate_fn=collate):
            optimizer.zero_grad()
            loss = model(**{k: v.to(device) for k, v in batch.items()}).loss
            if not torch.isfinite(loss):
                raise ValueError("non-finite loss")
            loss.backward()
            torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 1.)
            optimizer.step()
    def predictions(name):
        model.eval()
        logits, labels = [], []
        with torch.no_grad():
            for batch in DataLoader(encoded[name], batch_size=batch_size, collate_fn=collate):
                labels.extend(batch.pop("labels").tolist())
                logits.extend(model(**{k: v.to(device) for k, v in batch.items()}).logits.cpu().tolist())
        return logits, labels
    calibration_logits, calibration_labels = predictions("calibration")
    temperature = fit_temperature(calibration_logits, calibration_labels)
    calibration_p = [softmax(x, temperature) for x in calibration_logits]
    threshold = choose_threshold(calibration_p, calibration_labels)
    test_logits, test_labels = predictions("test")
    test_p = [softmax(x, temperature) for x in test_logits]
    test_report = report(test_p, test_labels, threshold)
    output.mkdir(parents=True)
    model.save_pretrained(output, safe_serialization=True)
    tokenizer.save_pretrained(output)
    metadata = {"schema_version": 1, "parameters": count, "trainable_parameters": trainable,
                "labels": list(LABELS), "temperature": temperature, "allow_min": threshold,
                "max_length": max_length, "mode": "full_finetune" if full_finetune else "frozen_backbone_head",
                "smoke_only": smoke, "deployment_validated": False}
    (output / "guard.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (output / "test-report.json").write_text(json.dumps(test_report, indent=2) + "\n")
    return metadata, test_report


def smoke_run(output):
    import torch
    from tokenizers import Tokenizer
    from tokenizers.models import WordLevel
    from tokenizers.pre_tokenizers import Whitespace
    from transformers import PreTrainedTokenizerFast, Qwen3Config, Qwen3ForSequenceClassification
    torch.manual_seed(42)
    vocab = {"<pad>": 0, "<unk>": 1, "read": 2, "delete": 3}
    core = Tokenizer(WordLevel(vocab=vocab, unk_token="<unk>"))
    core.pre_tokenizer = Whitespace()
    tokenizer = PreTrainedTokenizerFast(tokenizer_object=core, pad_token="<pad>", unk_token="<unk>")
    model = Qwen3ForSequenceClassification(Qwen3Config(vocab_size=4, hidden_size=32, intermediate_size=64,
        num_hidden_layers=1, num_attention_heads=2, num_key_value_heads=1, head_dim=16,
        max_position_embeddings=512, num_labels=3, pad_token_id=0, id2label=dict(enumerate(LABELS)), label2id={v:i for i,v in enumerate(LABELS)}))
    splits = {}
    for split in ("train", "calibration", "test"):
        splits[split] = [{"id": f"{split}-{i}", "user_intent": "read", "environment": {"fixture": split},
                          "tool": {"name": "read", "arguments": {"fixture": i}}, "label": {"decision": label}}
                         for i, label in enumerate(LABELS)]
    return run_training(model, tokenizer, splits, output, max_length=512, smoke=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", help="Directory produced by small_auto_mode.dataset")
    parser.add_argument("--output", required=True)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--max-length", type=int, default=4096)
    parser.add_argument("--full-finetune", action="store_true")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--smoke", action="store_true", help="Tiny RANDOM Qwen architecture; tests plumbing, never quality")
    args = parser.parse_args()
    if args.smoke:
        metadata, _ = smoke_run(args.output)
    else:
        if not args.data:
            parser.error("--data is required")
        splits, manifest = verified_splits(args.data)
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        torch.manual_seed(42)
        tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, revision=BASE_REVISION, trust_remote_code=False)
        tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token
        model = AutoModelForSequenceClassification.from_pretrained(BASE_MODEL, revision=BASE_REVISION,
            trust_remote_code=False, use_safetensors=True, num_labels=3, id2label=dict(enumerate(LABELS)), label2id={v:i for i,v in enumerate(LABELS)})
        model.config.pad_token_id = tokenizer.pad_token_id
        metadata, _ = run_training(model, tokenizer, splits, args.output, epochs=args.epochs,
            batch_size=args.batch_size, max_length=args.max_length, full_finetune=args.full_finetune, device=args.device)
        metadata.update(base_model=BASE_MODEL, base_revision=BASE_REVISION, dataset_manifest=manifest)
        Path(args.output, "guard.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    main()
