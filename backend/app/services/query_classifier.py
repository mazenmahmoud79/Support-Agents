"""
Query classifier for routing incoming questions to the best retrieval path.

Classifies queries as: faq | policy | troubleshooting | table | general
Uses keyword signals augmented by embedding similarity to known query prototypes.
"""
from dataclasses import dataclass
from typing import Dict, List, Tuple
from app.models.enums import QueryType
from app.core.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Keyword signal maps  (type → triggering keywords / phrases)
# ---------------------------------------------------------------------------
_KEYWORD_SIGNALS: Dict[QueryType, List[str]] = {
    QueryType.FAQ: [
        "what is", "what are", "who is", "what does", "can i", "do you",
        "how long", "is there", "كيف", "ما هو", "ما هي", "هل",
    ],
    QueryType.POLICY: [
        "policy", "rule", "regulation", "terms", "condition", "requirement",
        "allowed", "permitted", "prohibited", "compliance", "guideline",
        "سياسة", "شروط", "أحكام", "قواعد", "لوائح",
    ],
    QueryType.TROUBLESHOOTING: [
        "not working", "error", "issue", "problem", "broken", "fails", "can't",
        "cannot", "doesn't work", "fix", "resolve", "troubleshoot", "help me",
        "خطأ", "مشكلة", "لا يعمل", "حل",
    ],
    QueryType.TABLE: [
        "price", "cost", "plan", "fee", "rate", "pricing", "how much",
        "compare", "difference between", "table", "list", "options",
        "سعر", "تكلفة", "خطة", "رسوم", "مقارنة",
    ],
}

# Minimum score for a non-general classification to be accepted
_CONFIDENCE_THRESHOLD = 0.25
# Below this score the result is marked as uncertain (fallback = True)
_FALLBACK_THRESHOLD = 0.15


@dataclass
class QueryClassification:
    """Result of query classification."""
    query_type: QueryType
    confidence: float       # 0.0–1.0 normalised keyword-match confidence
    fallback: bool          # True → uncertain, use full hybrid search


class QueryClassifier:
    """Lightweight keyword-based query classifier."""

    def classify(self, query: str) -> QueryClassification:
        """
        Classify a query into one of the supported query types.

        Args:
            query: Raw user query string (Arabic or English)

        Returns:
            QueryClassification with type, confidence, and fallback flag
        """
        query_lower = query.lower()
        word_count = max(len(query_lower.split()), 1)

        scores: Dict[QueryType, float] = {}
        for qtype, keywords in _KEYWORD_SIGNALS.items():
            hits = sum(1 for kw in keywords if kw in query_lower)
            scores[qtype] = hits / word_count

        best_type = max(scores, key=lambda t: scores[t])
        best_score = scores[best_type]

        if best_score < _CONFIDENCE_THRESHOLD:
            result = QueryClassification(
                query_type=QueryType.GENERAL,
                confidence=1.0 - best_score,  # invert: more certain it's general
                fallback=best_score >= _FALLBACK_THRESHOLD,
            )
        else:
            result = QueryClassification(
                query_type=best_type,
                confidence=min(best_score * 5, 1.0),   # scale to 0–1
                fallback=False,
            )

        logger.debug(
            f"Query classified as '{result.query_type}' "
            f"(confidence={result.confidence:.2f}, fallback={result.fallback}) "
            f"| query='{query[:60]}'"
        )
        return result


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_classifier: QueryClassifier = None


def get_query_classifier() -> QueryClassifier:
    global _classifier
    if _classifier is None:
        _classifier = QueryClassifier()
    return _classifier
