import os


class EmbeddingUnavailableError(RuntimeError):
    """Raised when the configured Sentence Transformer cannot be loaded."""


class SentenceEmbeddingService:
    _model = None

    def __init__(self, model_name=None):
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    def _load_model(self):
        if self.__class__._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self.__class__._model = SentenceTransformer(self.model_name)
            except Exception as exc:
                raise EmbeddingUnavailableError(
                    f"Unable to load Sentence Transformer model '{self.model_name}'. "
                    "Pre-download the model or configure EMBEDDING_MODEL."
                ) from exc
        return self.__class__._model

    def encode(self, texts):
        model = self._load_model()
        return model.encode(texts, normalize_embeddings=True)

