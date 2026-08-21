from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CREED API"
    app_env: str = "development"
    app_version: str = "0.94.6"
    frontend_origin: str = "http://localhost:3000"
    database_url: str | None = None

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3.5:9b"
    ollama_runtime_model: str | None = "qwen3.5:4b"
    ollama_investigation_model: str | None = "qwen3.5:4b"
    ollama_learning_model: str | None = "qwen3.5:4b"
    ollama_timeout_seconds: float = 45.0
    ollama_investigation_timeout_seconds: float = 45.0
    ollama_learning_timeout_seconds: float = 180.0
    learning_context_window: int = 8192
    learning_num_predict: int = 900
    learning_excerpt_chars: int = 1400
    learning_generation_attempts: int = 3
    ollama_health_timeout_seconds: float = 5.0
    ollama_keep_alive: str = "30m"
    ollama_warm_on_startup: bool = True
    qwen_log_path: str = ".data/qwen-runs.jsonl"
    document_storage_path: str = ".data/documents"
    max_document_bytes: int = 20 * 1024 * 1024
    analysis_use_fast_issue_capsule: bool = True

    embedding_provider: str = "ollama"
    embedding_model: str = "qwen3-embedding:0.6b"
    embedding_dimensions: int = 384
    embedding_timeout_seconds: float = 45.0
    embedding_allow_hash_fallback: bool = True
    retrieval_keyword_only_max_chunks: int = 64
    chunk_size_chars: int = 1200
    chunk_overlap_chars: int = 180
    retrieval_semantic_weight: float = 0.55
    retrieval_keyword_weight: float = 0.35
    retrieval_metadata_weight: float = 0.10

    langgraph_checkpoint_path: str = ".data/langgraph-checkpoints.sqlite"
    analysis_event_poll_seconds: float = 0.35
    analysis_event_max_seconds: float = 600.0

    discovery_top_k: int = 8
    discovery_query_limit: int = 3
    discovery_issue_link_boost: float = 0.08
    discovery_query_coverage_bonus: float = 0.03
    discovery_min_base_score: float = 0.20
    investigation_top_k: int = 3
    investigation_max_docs: int = 2
    investigation_excerpt_chars: int = 450
    investigation_authoritative_config_chars: int = 2400
    investigation_issue_chars: int = 220
    investigation_num_predict: int = 170
    investigation_context_window: int = 2048
    investigation_retry_min_seconds: float = 8.0
    investigation_use_heuristic_fast_path: bool = False

    impact_method_weight: float = 0.35
    impact_module_weight: float = 0.20
    impact_fsd_weight: float = 0.15
    impact_configuration_weight: float = 0.10
    impact_history_weight: float = 0.10
    impact_semantic_weight: float = 0.10

    human_review_max_cycles: int = 3
    demo_mode_enabled: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def qwen_log_file(self) -> Path:
        return Path(self.qwen_log_path)

    @property
    def document_storage_dir(self) -> Path:
        path = Path(self.document_storage_path).expanduser()
        if path.is_absolute():
            return path.resolve()
        # Anchor relative document storage to the backend package root instead of
        # the process working directory. This keeps original-source paths stable
        # when Uvicorn is restarted from a different directory.
        backend_root = Path(__file__).resolve().parents[2]
        return (backend_root / path).resolve()

    @property
    def live_runtime_model(self) -> str:
        return self.ollama_runtime_model or self.ollama_investigation_model or self.ollama_model


@lru_cache
def get_settings() -> Settings:
    return Settings()
