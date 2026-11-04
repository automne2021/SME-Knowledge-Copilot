"""Code gọi model. Output của model luôn được validate trước khi vào services.

Module dự kiến:
- llm_client.py: adapter OpenAI-compatible, cấu hình qua LLM_BASE_URL/LLM_MODEL/LLM_API_KEY (M1).
- transcription.py: faster-whisper, trả segments có timestamp (M1).
- extraction.py: summary + action items, prompt nhận meeting_date và timezone (M1).
- embeddings.py, agent.py, tools/: M2.
"""
