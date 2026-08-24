"""
Theonix Core — Model Router.
Intelligently dispatches requests between Qwen 2.5-Coder 1.5B (Fast) and Qwen 3.5 4B (Quality).
"""

from typing import List, Dict, Optional


class ModelRouter:
    """Routes queries to the optimal local model based on intent and task complexity."""

    FAST_MODEL = "1.5b"       # Qwen 2.5-Coder 1.5B (Ultra-fast, low memory)
    QUALITY_MODEL = "4b"      # Qwen 3.5 4B (Deep reasoning, long context)

    @classmethod
    def select_model(cls, prompt: str, context_len: int = 0, user_preference: str = "auto") -> str:
        """
        user_preference: 'auto' | '1.5b' | '4b' | 'fast' | 'quality'
        """
        if user_preference in ["1.5b", "fast"]:
            return cls.FAST_MODEL
        if user_preference in ["4b", "quality"]:
            return cls.QUALITY_MODEL

        # Automatic Routing Heuristics
        p_lower = prompt.lower()

        # If context is very long (> 5,000 chars) -> Use Quality Model (larger context window)
        if context_len > 5000:
            return cls.QUALITY_MODEL

        # Heavy reasoning / Comparison / Multi-step questions -> 4B
        reasoning_keywords = [
            "compare", "difference between", "pros and cons", "analyze", "evaluate",
            "explain why", "step by step", "essay", "architecture", "in-depth"
        ]
        if any(kw in p_lower for kw in reasoning_keywords):
            return cls.QUALITY_MODEL

        # Code extraction, quick shell commands, simple QA, summaries -> 1.5B
        return cls.FAST_MODEL
