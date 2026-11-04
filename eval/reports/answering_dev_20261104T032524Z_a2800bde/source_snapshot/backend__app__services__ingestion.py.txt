"""Shared parse/chunk entry point for the future worker and offline evaluation."""

from app.services.chunking import ChunkConfig, split_document
from app.services.parsing import ParseLimits, parse_file


def prepare_document(path, file_format, settings, counter):
    limits = ParseLimits(
        max_pdf_pages=settings.max_pdf_pages,
        max_docx_uncompressed_mb=settings.max_docx_uncompressed_mb,
        max_docx_zip_entries=settings.max_docx_zip_entries,
        max_extracted_chars=settings.max_extracted_chars,
        max_source_blocks=settings.max_source_blocks,
        timeout_seconds=settings.parser_timeout_seconds,
    )
    parsed = parse_file(path, file_format, limits)
    chunks = split_document(
        parsed,
        counter,
        ChunkConfig(
            settings.chunk_size_tokens, settings.chunk_overlap_tokens, settings.max_document_chunks
        ),
    )
    return parsed, chunks
