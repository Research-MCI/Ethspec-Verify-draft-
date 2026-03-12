import math
from typing import Dict, Any


class SemanticScorer:
    def __init__(self, spec_keywords=None):
        self.spec_keywords = spec_keywords or []

    # -------------------------
    # Public scoring method
    # -------------------------
    def score(self, ast: Dict[str, Any]) -> float:
        structure = self._structure_score(ast)
        behavior = self._behavior_score(ast)
        coverage = self._keyword_coverage_score(ast)
        richness = self._richness_score(ast)

        final = (
            structure * 0.3 +
            behavior  * 0.3 +
            coverage  * 0.2 +
            richness  * 0.2
        )

        return round(final, 4)

    # -------------------------
    # 1️⃣ Structure Depth
    # -------------------------
    def _structure_score(self, ast):
        depth = self._max_depth(ast)
        return min(depth / 5, 1.0)  # normalized to [0,1]

    def _max_depth(self, obj, current=0):
        if isinstance(obj, dict):
            return max(
                [self._max_depth(v, current + 1) for v in obj.values()] + [current]
            )
        elif isinstance(obj, list):
            return max(
                [self._max_depth(v, current + 1) for v in obj] + [current]
            )
        return current

    # -------------------------
    # 2️⃣ Behavioral Elements
    # -------------------------
    def _behavior_score(self, ast):
        keys = self._flatten_keys(ast)

        behavioral_indicators = [
            "condition",
            "guard",
            "transition",
            "state",
            "effect",
            "action",
            "update"
        ]

        count = sum(1 for k in keys if k in behavioral_indicators)
        return min(count / 5, 1.0)

    # -------------------------
    # 3️⃣ Spec Keyword Coverage
    # -------------------------
    def _keyword_coverage_score(self, ast):
        if not self.spec_keywords:
            return 0.5  # neutral if no keywords provided

        text = str(ast).lower()
        matched = sum(1 for kw in self.spec_keywords if kw.lower() in text)

        return matched / len(self.spec_keywords)

    # -------------------------
    # 4️⃣ Richness (Node Count)
    # -------------------------
    def _richness_score(self, ast):
        node_count = self._count_nodes(ast)
        return min(node_count / 15, 1.0)

    def _count_nodes(self, obj):
        if isinstance(obj, dict):
            return 1 + sum(self._count_nodes(v) for v in obj.values())
        elif isinstance(obj, list):
            return 1 + sum(self._count_nodes(v) for v in obj)
        return 1

    # -------------------------
    # Utilities
    # -------------------------
    def _flatten_keys(self, obj):
        keys = set()

        if isinstance(obj, dict):
            for k, v in obj.items():
                keys.add(k)
                keys.update(self._flatten_keys(v))
        elif isinstance(obj, list):
            for item in obj:
                keys.update(self._flatten_keys(item))

        return keys

    
    def select_best_ast(ast_candidates, scorer, threshold=0.6):
        scored = [(ast, scorer.score(ast)) for ast in ast_candidates]
        scored.sort(key=lambda x: x[1], reverse=True)

        best_ast, best_score = scored[0]

        if best_score < threshold:
            raise ValueError("Error: Trivial AST")

        return best_ast, best_score