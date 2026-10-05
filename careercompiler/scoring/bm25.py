"""Deterministic Okapi BM25 implementation for resume and JD requirement scoring."""

import math
import re
from collections import Counter
from collections.abc import Sequence

from careercompiler.extraction.models import ExtractedJD
from careercompiler.scoring.models import BM25Config, ScorableBullet


def tokenize_text(text: str) -> list[str]:
    """Tokenize text preserving technical identifiers like C++, C#, .NET, Node.js."""
    # Normalize common technical compounds
    normalized = text.lower()
    normalized = normalized.replace("c++", " cplusplus ")
    normalized = normalized.replace("c#", " csharp ")
    normalized = normalized.replace(".net", " dotnet ")
    normalized = normalized.replace("node.js", " nodejs ")

    # Extract alphanumeric tokens
    tokens = re.findall(r"[a-z0-9]+(?:[-_][a-z0-9]+)*", normalized)
    return [t for t in tokens if len(t) > 1 or t in {"c", "r"}]


class BM25Index:
    """Inverted index and BM25 scorer over a background document corpus."""

    def __init__(self, corpus: Sequence[str], config: BM25Config | None = None) -> None:
        self.config = config or BM25Config()
        self.k1 = self.config.k1
        self.b = self.config.b

        self.N = len(corpus)
        self.doc_lengths: list[int] = []
        self.doc_term_freqs: list[Counter[str]] = []
        self.doc_freqs: Counter[str] = Counter()

        total_length = 0
        for doc in corpus:
            tokens = tokenize_text(doc)
            length = len(tokens)
            self.doc_lengths.append(length)
            total_length += length

            tf: Counter[str] = Counter(tokens)
            self.doc_term_freqs.append(tf)
            for term in tf:
                self.doc_freqs[term] += 1

        self.avgdl = (total_length / self.N) if self.N > 0 else 1.0
        self.idf_cache: dict[str, float] = {}

    def get_idf(self, term: str) -> float:
        """Compute or retrieve cached Okapi IDF for term."""
        if term in self.idf_cache:
            return self.idf_cache[term]

        n = self.doc_freqs.get(term, 0)
        # Standard Okapi IDF with +1.0 floor
        idf = math.log((self.N - n + 0.5) / (n + 0.5) + 1.0)
        self.idf_cache[term] = idf
        return idf

    def score_query_against_doc_tokens(self, query_tokens: Sequence[str], doc_tokens: Sequence[str]) -> float:
        """Score an ad-hoc document against a query using the corpus IDF and average document length."""
        doc_len = len(doc_tokens)
        if doc_len == 0 or len(query_tokens) == 0:
            return 0.0

        doc_tf: Counter[str] = Counter(doc_tokens)
        score = 0.0

        for q in query_tokens:
            tf = doc_tf.get(q, 0)
            if tf == 0:
                continue
            idf = self.get_idf(q)
            numerator = tf * (self.k1 + 1.0)
            denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avgdl))
            score += idf * (numerator / denominator)

        return score


class BM25Scorer:
    """Scorer coordinating corpus indexing and selection scoring."""

    def __init__(self, config: BM25Config | None = None) -> None:
        self.config = config or BM25Config()

    def build_corpus(
        self,
        bank_bullets: Sequence[str],
        jd_requirements: Sequence[str],
    ) -> list[str]:
        """Build background corpus according to configured corpus mode."""
        mode = self.config.corpus_mode
        if mode == "bank_only":
            return list(bank_bullets)
        elif mode == "jd_only":
            return list(jd_requirements)
        else:  # "bank_plus_jd" default
            return list(bank_bullets) + list(jd_requirements)

    def score_selection(
        self,
        bullets: Sequence[ScorableBullet],
        jd: ExtractedJD,
        bank_bullet_texts: Sequence[str] | None = None,
    ) -> float:
        """Score a selection of bullets against JD requirements using BM25."""
        reqs = jd.all_requirements
        if len(reqs) == 0:
            return 100.0
        if len(bullets) == 0:
            return 0.0

        # Build corpus
        req_texts = [r.evidence_text for r in reqs]
        bank_texts = list(bank_bullet_texts or [b.text for b in bullets])
        corpus = self.build_corpus(bank_texts, req_texts)

        index = BM25Index(corpus, self.config)

        bullet_token_lists = [tokenize_text(b.text) for b in bullets]

        total_normalized_score = 0.0
        for req in reqs:
            query_tokens = tokenize_text(req.evidence_text)
            if not query_tokens:
                continue

            max_bm25 = 0.0
            for b_tokens in bullet_token_lists:
                s = index.score_query_against_doc_tokens(query_tokens, b_tokens)
                if s > max_bm25:
                    max_bm25 = s

            # Soft saturation via tanh(max_bm25 / k_norm)
            norm = math.tanh(max_bm25 / self.config.k_norm)
            total_normalized_score += norm

        raw_score = 100.0 * (total_normalized_score / len(reqs))
        return min(100.0, max(0.0, round(raw_score, 4)))

    def score_single_bullet(
        self,
        bullet_text: str,
        jd: ExtractedJD,
        bank_bullet_texts: Sequence[str] | None = None,
    ) -> float:
        """Score a single bullet text against all JD requirements."""
        bullet_obj = ScorableBullet(id="temp", text=bullet_text)
        return self.score_selection([bullet_obj], jd, bank_bullet_texts)
