import os
from pathlib import Path


class EmbeddingUnavailableError(RuntimeError):
    """Raised when the configured Sentence Transformer cannot be loaded."""


class SentenceEmbeddingService:
    _model = None
    _model_load_error = None

    def __init__(self, model_name=None):
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    def _is_model_cached(self):
        model_path = Path(self.model_name).expanduser()
        if model_path.exists():
            return True

        model_cache_name = f"models--{self.model_name.replace('/', '--')}"
        home = Path.home()
        huggingface_root = Path(os.getenv("HF_HOME", home / ".cache" / "huggingface"))
        hub_root = Path(os.getenv("HF_HUB_CACHE", huggingface_root / "hub"))
        sentence_transformers_root = Path(os.getenv("SENTENCE_TRANSFORMERS_HOME", home / ".cache" / "torch" / "sentence_transformers"))
        return (hub_root / model_cache_name).is_dir() or (sentence_transformers_root / self.model_name).is_dir()

    def _load_model(self):
        if self.__class__._model_load_error:
            raise EmbeddingUnavailableError(self.__class__._model_load_error)
        if self.__class__._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                local_only_setting = os.getenv("EMBEDDING_LOCAL_FILES_ONLY")
                local_files_only = (
                    local_only_setting.lower() in {"1", "true", "yes"}
                    if local_only_setting is not None
                    else os.getenv("DJANGO_DEBUG", "True").lower() in {"1", "true", "yes"}
                )
                if local_files_only and not self._is_model_cached():
                    raise FileNotFoundError(f"Sentence Transformer model '{self.model_name}' is not cached locally.")
                self.__class__._model = SentenceTransformer(self.model_name, local_files_only=local_files_only)
            except Exception as exc:
                message = (
                    f"Unable to load Sentence Transformer model '{self.model_name}'. "
                    "Semantic matching is unavailable until the model is cached or configured."
                )
                self.__class__._model_load_error = message
                raise EmbeddingUnavailableError(message) from exc
        return self.__class__._model

    def encode(self, texts):
        model = self._load_model()
        return model.encode(texts, normalize_embeddings=True)
