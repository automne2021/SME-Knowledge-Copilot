"""Structure-first chunks with exact spans, bounded overlap and offline E5 token counts."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol

from app.services.parsing import ParsedDocument, ParseError

CHUNKER_VERSION = "structure-e5-v1"
E5_MODEL = "intfloat/multilingual-e5-small"
E5_REVISION = "614241f622f53c4eeff9890bdc4f31cfecc418b3"


class TokenCounter(Protocol):
    def count(self, text: str) -> int: ...


class E5TokenCounter:
    """No torch/weights, no auto download, no padding/truncation."""

    def __init__(self, cache_dir):
        from huggingface_hub import hf_hub_download
        from tokenizers import Tokenizer

        path = hf_hub_download(
            E5_MODEL,
            "tokenizer.json",
            revision=E5_REVISION,
            cache_dir=str(cache_dir),
            local_files_only=True,
        )
        self.tokenizer = Tokenizer.from_file(path)
        self.tokenizer.no_truncation()
        self.tokenizer.no_padding()

    def count(self, text: str) -> int:
        return len(self.tokenizer.encode("passage: " + text, add_special_tokens=True).ids)

    def count_query(self, text: str) -> int:
        return len(self.tokenizer.encode("query: " + text, add_special_tokens=True).ids)


@dataclass(frozen=True)
class ChunkConfig:
    size_tokens: int = 350
    overlap_tokens: int = 50
    max_chunks: int = 5000

    def __post_init__(self):
        if not 0 <= self.overlap_tokens < self.size_tokens <= 512 or self.max_chunks < 1:
            raise ValueError("Invalid E5 chunk budget")


@dataclass
class TextChunk:
    chunk_index: int
    text: str
    text_sha256: str
    token_count: int
    location: dict
    source_spans: list[dict]


def split_document(
    document: ParsedDocument, counter: TokenCounter, config: ChunkConfig | None = None
) -> list[TextChunk]:
    config = config or ChunkConfig()
    by_id = {block.block_id: block for block in document.blocks}
    chunks: list[TextChunk] = []
    pending: list[dict] = []
    pending_key = None

    def text_of(spans):
        return "\n".join(
            by_id[s["block_id"]].normalized_text[s["char_start"] : s["char_end"]] for s in spans
        )

    def span(block, start, end, role="content"):
        return {"block_id": block.block_id, "char_start": start, "char_end": end, "role": role}

    def fits(spans):
        text = text_of(spans)
        # Bound tokenizer work for pathological huge paragraphs or context headers.
        return len(text) <= config.size_tokens * 32 and counter.count(text) <= config.size_tokens

    def emit(spans):
        text = text_of(spans)
        count = counter.count(text)
        if not text.strip() or count > config.size_tokens or count > 512:
            raise ParseError("document_limit_exceeded")
        if len(chunks) >= config.max_chunks:
            raise ParseError("document_limit_exceeded")
        locations = [by_id[s["block_id"]].location for s in spans if s["role"] == "content"]
        location = {"kind": locations[0]["kind"], "locations": locations}
        for axis in ("page", "line", "block", "row"):
            if all(f"{axis}_start" in item and f"{axis}_end" in item for item in locations):
                location[f"{axis}_start"] = min(item[f"{axis}_start"] for item in locations)
                location[f"{axis}_end"] = max(item[f"{axis}_end"] for item in locations)
        if all(item.get("table") == locations[0].get("table") for item in locations):
            if "table" in locations[0]:
                location["table"] = locations[0]["table"]
        chunks.append(
            TextChunk(
                len(chunks),
                text,
                hashlib.sha256(text.encode()).hexdigest(),
                count,
                location,
                spans,
            )
        )

    for block in document.blocks:
        # Never cross a PDF page or a heading/table-header context boundary.
        key = (block.location.get("page_start"), tuple(block.context_ids), block.location["kind"])
        if pending and key != pending_key:
            emit(pending)
            pending = []
        pending_key = key
        context = [
            span(by_id[item], 0, len(by_id[item].normalized_text), "context")
            for item in block.context_ids
        ]
        whole = span(block, 0, len(block.normalized_text))
        candidate = pending + [whole] if pending else context + [whole]
        if fits(candidate):
            pending = candidate
            continue
        if pending:
            emit(pending)
            pending = []
        if fits(context + [whole]):
            pending = context + [whole]
            continue
        # An oversized block is split by Unicode code points. Every substring is recounted;
        # final correctness does not assume tokenizer counts are mathematically monotone.
        start = 0
        if not fits(context):
            raise ParseError("document_limit_exceeded")
        while start < len(block.normalized_text):
            low, high = start + 1, min(len(block.normalized_text), start + config.size_tokens * 32)
            end = start
            while low <= high:
                middle = (low + high) // 2
                if (
                    counter.count(text_of(context + [span(block, start, middle)]))
                    <= config.size_tokens
                ):
                    end, low = middle, middle + 1
                else:
                    high = middle - 1
            if end == start:
                raise ParseError("document_limit_exceeded")
            # Prefer a word boundary, without discarding any character between slices.
            boundary = block.normalized_text.rfind(" ", start + 1, end)
            if end < len(block.normalized_text) and boundary > start + (end - start) // 2:
                end = boundary + 1
            emit(context + [span(block, start, end)])
            if end == len(block.normalized_text):
                break
            next_start = end
            if config.overlap_tokens:
                # Count overlap without the E5 wrapper: subtract the empty input overhead.
                low, high = start + 1, end
                while low <= high:
                    middle = (low + high) // 2
                    overlap = block.normalized_text[middle:end]
                    if counter.count(overlap) - counter.count("") <= config.overlap_tokens:
                        next_start, high = middle, middle - 1
                    else:
                        low = middle + 1
            start = max(start + 1, next_start)
    if pending:
        emit(pending)
    return chunks
