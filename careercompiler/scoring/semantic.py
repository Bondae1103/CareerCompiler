"""Deterministic local and offline semantic embedding providers and scorers."""

import hashlib
import math
from abc import ABC, abstractmethod
from collections.abc import Sequence

from careercompiler.extraction.models import ExtractedJD
from careercompiler.scoring.models import ScorableBullet, SemanticConfig


class BaseEmbedder(ABC):
    """Abstract base class for semantic text embedding."""

    @abstractmethod
    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """Compute normalized dense embedding vectors for a batch of texts."""
        pass


class DeterministicHashingEmbedder(BaseEmbedder):
    """Deterministic, 100% offline embedder using hashed character and subword n-grams.

    Operates without PyTorch, neural models, or external networks. Computes signed feature
    hash projections into an L2-normalized hypersphere.
    """

    def __init__(self, config: SemanticConfig | None = None) -> None:
        self.config = config or SemanticConfig()
        self.dim = self.config.embedding_dim
        self.ngram_min = self.config.ngram_min
        self.ngram_max = self.config.ngram_max
        self._cache: dict[str, list[float]] = {}

    def _hash_token(self, token: str) -> tuple[int, float]:
        """Hash a token to an index and sign (+1.0 or -1.0)."""
        h = hashlib.sha256(token.encode("utf-8")).digest()
        idx = int.from_bytes(h[:4], "big") % self.dim
        sign = 1.0 if (h[4] & 1) == 0 else -1.0
        return idx, sign

    def embed_single(self, text: str) -> list[float]:
        """Embed a single text string into a normalized dense vector."""
        if text in self._cache:
            return self._cache[text]

        vec = [0.0] * self.dim
        clean_text = text.lower().strip()
        if not clean_text:
            return vec

        # Word tokens
        words = clean_text.split()
        for w in words:
            idx, sign = self._hash_token(f"w_{w}")
            vec[idx] += 2.0 * sign

        # Subword character n-grams
        for n in range(self.ngram_min, self.ngram_max + 1):
            for i in range(len(clean_text) - n + 1):
                ngram = clean_text[i : i + n]
                idx, sign = self._hash_token(f"c_{ngram}")
                vec[idx] += 1.0 * sign

        # L2 Normalize
        norm_sq = sum(x * x for x in vec)
        if norm_sq > 0.0:
            norm = math.sqrt(norm_sq)
            vec = [round(x / norm, 6) for x in vec]

        self._cache[text] = vec
        return vec

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed a sequence of texts."""
        return [self.embed_single(t) for t in texts]


def cosine_similarity(v1: Sequence[float], v2: Sequence[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(a * b for a, b in zip(v1, v2, strict=False))
    # If vectors are already unit-norm, dot is cosine
    return max(-1.0, min(1.0, dot))


class SemanticScorer:
    """Coordinates embedding generation and semantic similarity evaluation."""

    def __init__(
        self,
        config: SemanticConfig | None = None,
        embedder: BaseEmbedder | None = None,
    ) -> None:
        self.config = config or SemanticConfig()
        if embedder is not None:
            self.embedder = embedder
        else:
            self.embedder = DeterministicHashingEmbedder(self.config)

    def score_selection(
        self,
        bullets: Sequence[ScorableBullet],
        jd: ExtractedJD,
    ) -> float:
        """Compute semantic match score of a bullet selection against JD requirements."""
        reqs = jd.all_requirements
        if len(reqs) == 0:
            return 100.0
        if len(bullets) == 0:
            return 0.0

        bullet_texts = [b.text for b in bullets]
        bullet_vecs = self.embedder.embed_texts(bullet_texts)

        req_texts = [r.evidence_text for r in reqs]
        req_vecs = self.embedder.embed_texts(req_texts)

        total_sim = 0.0
        for r_vec in req_vecs:
            max_sim = 0.0
            for b_vec in bullet_vecs:
                sim = cosine_similarity(b_vec, r_vec)
                if sim > max_sim:
                    max_sim = sim
            total_sim += max(0.0, max_sim)

        score = 100.0 * (total_sim / len(req_vecs))
        return min(100.0, max(0.0, round(score, 4)))

    def score_single_bullet(
        self,
        bullet_text: str,
        jd: ExtractedJD,
    ) -> float:
        """Compute semantic match score for a single bullet text."""
        b = ScorableBullet(id="temp", text=bullet_text)
        return self.score_selection([b], jd)
