# Generates shared, normalized Sentence Transformer embeddings.

import threading
import math
import numpy as np

from app.core.config import settings


class EmbeddingModel:
    def __init__(self, model_name: str, device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self._model = None
        self._lock = threading.Lock()

    def _load(self):
        if self._model is None:
            with self._lock:
                if self._model is None:
                    try:
                        from sentence_transformers import SentenceTransformer
                        self._model = SentenceTransformer(
                            self.model_name,
                            device=self.device,
                            trust_remote_code=False,
                        )
                    except Exception as exc:
                        raise RuntimeError("The embedding model could not be loaded.") from exc
        return self._model

    @property
    def tokenizer(self):
        return getattr(self._load(), "tokenizer", None)

    @property
    def dimension(self) -> int:
        model = self._load()
        if hasattr(model, "get_embedding_dimension"):
            dimension = model.get_embedding_dimension()
        else:
            dimension = model.get_sentence_embedding_dimension()
        if not dimension:
            raise RuntimeError("The embedding model returned no dimension.")
        return int(dimension)

    def embed_documents(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        if not texts:
            return []
        vectors = self._load().encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return self._validate(vectors)

    def embed_query(self, text: str) -> list[float]:
        vectors = self.embed_documents([text], batch_size=1)
        if not vectors:
            raise RuntimeError("The query embedding is empty.")
        return vectors[0]

    def _validate(self, vectors) -> list[list[float]]:
        arrays = np.asarray(vectors, dtype=np.float32)
        if arrays.ndim != 2:
            raise RuntimeError("The embedding model returned invalid output.")
        if arrays.shape[0] == 0:
            return []
        if not np.isfinite(arrays).all():
            raise RuntimeError("The embedding model returned invalid numeric values.")
        dimension = int(self.dimension)
        if arrays.shape[1] != dimension:
            raise RuntimeError("The embedding dimension does not match the model.")
        return arrays.tolist()


_embedding_lock = threading.Lock()
_embedding_model: EmbeddingModel | None = None


def get_embedding_model() -> EmbeddingModel:
    global _embedding_model
    if _embedding_model is None:
        with _embedding_lock:
            if _embedding_model is None:
                _embedding_model = EmbeddingModel(settings.EMBEDDING_MODEL, settings.EMBEDDING_DEVICE)
    return _embedding_model
