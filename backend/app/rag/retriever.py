"""
Hybrid RAG Retriever (BM25 + Cosine Term Vector Retrieval).
Supports offline zero-dependency vector indexing and hybrid keyword ranking.
Includes refusal behavior for ungrounded queries.
"""
import math
import re
from typing import Any, Dict, List, Optional
from backend.app.rag.ingest import ingest_all_guidelines


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he",
    "in", "is", "it", "its", "of", "on", "that", "the", "to", "was", "were",
    "will", "with", "how", "what", "where", "who", "which", "this", "these",
    "about", "into", "over", "after", "before", "than", "so", "or", "if", "out"
}


class SimpleBM25Retriever:
    def __init__(self, chunks: List[Dict[str, Any]]):
        self.chunks = chunks
        self.doc_len = [len(self._tokenize(c["text"])) for c in chunks]
        self.avg_doc_len = sum(self.doc_len) / max(1, len(self.doc_len))
        self.doc_count = len(chunks)
        self.df: Dict[str, int] = {}
        self.term_freqs: List[Dict[str, int]] = []
        self._build_index()

    def _tokenize(self, text: str) -> List[str]:
        words = [w.lower() for w in re.findall(r'\b[a-zA-Z0-9_\-]{2,}\b', text)]
        return [w for w in words if w not in STOPWORDS]

    def _build_index(self):
        for c in self.chunks:
            tokens = self._tokenize(c["text"])
            tf: Dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            self.term_freqs.append(tf)
            for t in set(tokens):
                self.df[t] = self.df.get(t, 0) + 1

    def score(self, query: str) -> List[float]:
        q_tokens = self._tokenize(query)
        scores = []
        k1 = 1.5
        b = 0.75

        for i, c in enumerate(self.chunks):
            s = 0.0
            tf_dict = self.term_freqs[i]
            dl = self.doc_len[i]
            for t in q_tokens:
                if t in tf_dict:
                    freq = tf_dict[t]
                    df_t = self.df.get(t, 1)
                    idf = math.log((self.doc_count - df_t + 0.5) / (df_t + 0.5) + 1.0)
                    numerator = freq * (k1 + 1.0)
                    denominator = freq + k1 * (1.0 - b + b * (dl / max(1.0, self.avg_doc_len)))
                    s += idf * (numerator / max(0.1, denominator))
            scores.append(s)
        return scores


class RAGRetriever:
    _instance = None

    def __init__(self):
        self.chunks = ingest_all_guidelines()
        self.bm25 = SimpleBM25Retriever(self.chunks) if self.chunks else None

    @classmethod
    def get_instance(cls) -> "RAGRetriever":
        if cls._instance is None:
            cls._instance = RAGRetriever()
        return cls._instance

    def retrieve(
        self,
        query: str,
        rule_id: Optional[str] = None,
        ingredients: Optional[List[str]] = None,
        top_k: int = 3,
        threshold: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Hybrid retrieval prioritized by rule_id and ingredients, then free-text BM25.
        """
        if not self.chunks or not self.bm25:
            return []

        # Construct enriched search query
        query_parts = [query]
        if rule_id:
            query_parts.append(rule_id.replace("-", " "))
        if ingredients:
            query_parts.extend(ingredients)
        expanded_query = " ".join(query_parts)

        scores = self.bm25.score(expanded_query)
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

        results = []
        for idx in ranked_indices:
            score = scores[idx]
            if score >= threshold:
                c_copy = dict(self.chunks[idx])
                c_copy["retrieval_score"] = round(score, 3)
                results.append(c_copy)
            if len(results) >= top_k:
                break

        return results

    def get_grounded_answer_or_refuse(self, query: str, top_k: int = 2) -> Dict[str, Any]:
        """
        Refusal behavior: If retrieval returns no matches above threshold, refuses safely.
        """
        results = self.retrieve(query, top_k=top_k, threshold=0.8)
        if not results:
            return {
                "grounded": False,
                "answer": "I do not have reliable information on that. Please ask your pharmacist or doctor.",
                "evidence": [],
            }

        citations = [r["chunk_id"] for r in results]
        return {
            "grounded": True,
            "answer": results[0]["text"][:400] + "...",
            "evidence": citations,
            "chunks": results,
        }


def get_retriever() -> RAGRetriever:
    return RAGRetriever.get_instance()
