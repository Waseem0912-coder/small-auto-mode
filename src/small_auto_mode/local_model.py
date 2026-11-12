"""Local classification head adapter. Artifacts remain experimental by default."""
import json
from pathlib import Path
from .dataset import input_text
from .metrics import softmax


class LocalClassifier:
    def __init__(self, directory, device="cpu"):
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        self.torch, self.device = torch, device
        self.metadata = json.loads(Path(directory, "guard.json").read_text())
        if self.metadata.get("labels") != ["allow", "ask", "deny"]:
            raise ValueError("unsupported class order")
        self.tokenizer = AutoTokenizer.from_pretrained(directory, trust_remote_code=False, local_files_only=True)
        self.model = AutoModelForSequenceClassification.from_pretrained(directory, trust_remote_code=False, local_files_only=True, use_safetensors=True).to(device).eval()
        if sum(p.numel() for p in self.model.parameters()) > 1_000_000_000:
            raise ValueError("model exceeds 1B parameter budget")

    def __call__(self, case):
        encoded = self.tokenizer(input_text(case), truncation=False, return_token_type_ids=False, return_tensors="pt")
        if encoded['input_ids'].shape[1] > self.metadata['max_length']:
            raise ValueError("context too long")
        with self.torch.no_grad():
            logits = self.model(**{k:v.to(self.device) for k,v in encoded.items()}).logits[0].cpu().tolist()
        return dict(zip(self.metadata['labels'], softmax(logits, self.metadata['temperature'])))
