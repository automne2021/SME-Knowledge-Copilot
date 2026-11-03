"""Fail-closed canonical-to-active generation loader; external corpus version != DB counter."""

from sqlalchemy import select

from app.models import Chunk, Document, DocumentRevision, SourceBlock
from app.services.parsing import normalize


def load_active_mapping(db, workspace_id, uploaded, mapping, profile):
    block_maps, chunk_spans, chunk_text = {}, {}, {}
    for reference, expected in mapping["documents"].items():
        document = db.get(Document, uploaded[reference])
        if document is None or document.workspace_id != workspace_id or document.status != "ready":
            raise ValueError("Corpus document missing/not active in evaluation scope")
        revision = db.get(DocumentRevision, document.active_revision_id)
        if (
            document.sha256 != expected["sha256"]
            or revision is None
            or revision.status != "ready"
            or revision.parser_version != mapping["parser_version"]
            or revision.index_version != profile["index_version"]
            or revision.embedding_fingerprint != profile["embedding_fingerprint"]
        ):
            raise ValueError("Corpus/parser/index fingerprint drift")
        blocks = db.scalars(
            select(SourceBlock)
            .where(
                SourceBlock.revision_id == revision.id,
                SourceBlock.generation_id == document.active_generation_id,
            )
            .order_by(SourceBlock.block_index)
        ).all()
        if len(blocks) != len(expected["blocks"]):
            raise ValueError("Parser block count drift")
        by_parser, reverse = {}, {}
        for block, gold in zip(blocks, expected["blocks"], strict=True):
            location = {
                key: value
                for key, value in block.location_json.items()
                if key not in {"parser_block_id", "context_block_ids"}
            }
            if (
                block.location_json.get("parser_block_id") != gold["block_id"]
                or block.normalized_text != gold["normalized_text"]
                or block.raw_text != gold["raw_text"]
                or location != gold["location"]
            ):
                raise ValueError("Parser block text/location drift")
            by_parser[gold["block_id"]] = {"id": str(block.id), "text": block.normalized_text}
            reverse[str(block.id)] = gold["block_id"]
        chunks = db.scalars(
            select(Chunk)
            .where(
                Chunk.revision_id == revision.id,
                Chunk.generation_id == document.active_generation_id,
            )
            .order_by(Chunk.chunk_index)
        ).all()
        if len(chunks) != len(expected["chunks"]):
            raise ValueError("Chunk count drift")
        for chunk, gold in zip(chunks, expected["chunks"], strict=True):
            converted = [
                {**span, "block_id": reverse.get(span["block_id"])}
                for span in chunk.source_spans_json
            ]
            if (
                chunk.text != gold["text"]
                or chunk.text_sha256 != gold["text_sha256"]
                or converted != gold["source_spans"]
                or chunk.location_json != gold["location"]
            ):
                raise ValueError("Chunk text/location/span drift")
            chunk_spans[str(chunk.id)], chunk_text[str(chunk.id)] = (
                chunk.source_spans_json,
                chunk.text,
            )
        block_maps[reference] = by_parser
    return {"blocks": block_maps, "chunk_spans": chunk_spans, "chunk_text": chunk_text}


def question_groups(question, mapped_question, loaded):
    if question["id"] != mapped_question["id"] or len(question["gold_evidence"]) != len(
        mapped_question["evidence"]
    ):
        raise ValueError("Question mapping drift")
    groups = {}
    for original, evidence in zip(
        question["gold_evidence"], mapped_question["evidence"], strict=True
    ):
        if (
            original["evidence_id"] != evidence["evidence_id"]
            or original["quote"] != evidence["quote"]
            or original["evidence_group_id"] != evidence["evidence_group_id"]
        ):
            raise ValueError("Evidence identity drift")
        spans, parts = [], []
        for span in evidence["parser_spans"]:
            actual = loaded["blocks"][evidence["document_id"]][span["block_id"]]
            spans.append({**span, "block_id": actual["id"]})
            parts.append(actual["text"][span["char_start"] : span["char_end"]])
        if normalize(" ".join(parts)) != normalize(evidence["quote"]):
            raise ValueError("Gold quote drift")
        groups.setdefault(evidence["evidence_group_id"], []).append(spans)
    return groups
