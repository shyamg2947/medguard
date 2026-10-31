# MedGuard Assumptions Log

This document records engineering and clinical-modeling assumptions made during development when specifications allowed multiple reasonable interpretations, per prompt.md Section 0 (Rule 2).

| Date | Topic | Assumption | Reason |
|------|-------|------------|--------|
| 2026-10-31 | Python Runtime | Target Python 3.11+ using native SQLite with SQLAlchemy 2.x and standard library JSON storage for complex structures. | Ensures portability across local development and docker containers without requiring an external DB by default. |
| 2026-10-31 | Passwords & Auth | Use PBKDF2/SHA256 via hashlib / passlib fallback for local authentication tokens and demo passwords. | Zero-dependency resilient auth across all OS environments without requiring external C compiler dependencies. |
| 2026-10-31 | Fernet Vault Key | Default dev VAULT_KEY generated with standard Fernet 32-byte urlsafe base64 if not explicitly provided in environment. | Allows zero-config demo boot while warning on production usage. |
| 2026-10-31 | Offline Embeddings & RAG | Provide a fast, lightweight cosine vector index alongside hybrid BM25 search that runs in-memory or on disk without requiring massive native model downloads in demo mode. | Guarantees instant startup and zero-network execution on any laptop. |
| 2026-10-31 | Single Frontend SPA | Build an elegant multi-app React SPA with tabbed/routed navigation between Landing, Senior PWA, Caregiver, Clinician Swipe, Admin, and WhatsApp Simulator. | Seamless live demonstration and unified Apple-inspired token system without multi-port orchestration friction. |
| 2026-10-31 | LLM Free-tier Model | Default `LLM_MODEL=gemini-2.5-flash` via Google GenAI SDK with graceful degradation to pre-translated verified rule text. | Gemini 2.5 Flash is standard and responsive on Google AI Studio free tier. |

