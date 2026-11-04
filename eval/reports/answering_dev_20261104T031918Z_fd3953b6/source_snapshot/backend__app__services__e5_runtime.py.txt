"""Shared CPU E5 inference used by production worker and compatibility smoke."""

from pathlib import Path


class InputTooLong(ValueError):
    """Reject complete prefixed inputs before inference, instead of truncating."""


def prepare_inputs(texts: list[str], kind: str) -> list[str]:
    if kind not in {"query", "passage"}:
        raise ValueError("Expected query or passage")
    if not texts or any(not isinstance(text, str) or not text.strip() for text in texts):
        raise ValueError("Embedding inputs must be nonempty strings")
    return [f"{kind}: {text}" for text in texts]


def check_lengths(tokenizer, inputs: list[str], limit: int = 512) -> list[int]:
    # Counts include prefix, heading and special tokens. Do not pass truncation=True.
    lengths = [len(ids) for ids in tokenizer(inputs, truncation=False)["input_ids"]]
    if any(length > limit for length in lengths):
        raise InputTooLong(f"Input exceeds {limit} tokens; maximum observed {max(lengths)}")
    return lengths


class E5Encoder:
    def __init__(self, snapshot: Path, threads: int = 2):
        import torch
        from transformers import AutoModel, AutoTokenizer

        torch.set_num_threads(threads)
        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(
            snapshot, local_files_only=True, trust_remote_code=False
        )
        self.model = (
            AutoModel.from_pretrained(
                snapshot,
                local_files_only=True,
                trust_remote_code=False,
                use_safetensors=True,
                dtype=torch.float32,
                attn_implementation="eager",
            )
            .to("cpu")
            .eval()
        )
        if self.model.config.hidden_size != 384:
            raise ValueError("E5 dimension mismatch")

    def encode(self, texts: list[str], kind: str, batch_size: int = 4):
        torch = self.torch
        inputs = prepare_inputs(texts, kind)
        check_lengths(self.tokenizer, inputs)
        if type(batch_size) is not int or batch_size < 1:
            raise ValueError("batch_size must be a positive integer")
        vectors = []
        with torch.inference_mode():
            for offset in range(0, len(inputs), batch_size):
                batch = self.tokenizer(
                    inputs[offset : offset + batch_size],
                    padding=True,
                    truncation=False,
                    return_tensors="pt",
                )
                hidden = self.model(**batch).last_hidden_state
                mask = batch["attention_mask"]
                hidden = hidden.masked_fill(~mask[..., None].bool(), 0.0)
                pooled = hidden.sum(dim=1) / mask.sum(dim=1)[..., None]
                vectors.append(torch.nn.functional.normalize(pooled, p=2, dim=1))
        result = torch.cat(vectors)
        if result.shape != (len(inputs), 384) or not torch.isfinite(result).all():
            raise ValueError("Invalid embedding shape or nonfinite vectors")
        return result
