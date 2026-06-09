from typing import Dict, Any


# ============================================================
# MODEL ROUTING POLICY
# ============================================================
class LLMRouter:
    """
    Decides which model should be used based on:
    - node type
    - game state context
    """

    def __init__(self):
        # central policy config (can later move to YAML)
        self.rules = {
            "narration": "qwen3:8b",
            "rules": "local-small",
            "fallback": "local-small",
        }

    # --------------------------------------------------------
    # SAFE ACCESS HELPERS
    # --------------------------------------------------------
    def _get(self, context: Dict[str, Any], key: str, default=0):
        return context.get(key, default)

    # --------------------------------------------------------
    # MAIN ROUTING LOGIC
    # --------------------------------------------------------
    def route_model(self, node_type: str, context: Dict[str, Any]) -> str:
        storm = self._get(context, "stormPressure", 0)
        trust = self._get(context, "guideTrust", 50)
        health = self._get(context, "health", 100)

        # ----------------------------------------------------
        # HIGH-RISK CONDITIONS → STRONG MODEL
        # ----------------------------------------------------
        if storm > 80 or health < 25:
            return "gpt-4o"

        # ----------------------------------------------------
        # LOW TRUST → BETTER MODEL FOR NUANCED NARRATION
        # ----------------------------------------------------
        if trust < 30 and node_type == "narration":
            return "qwen3:8b"

        # ----------------------------------------------------
        # NODE-SPECIFIC DEFAULTS
        # ----------------------------------------------------
        if node_type in self.rules:
            return self.rules[node_type]

        # ----------------------------------------------------
        # FALLBACK
        # ----------------------------------------------------
        return self.rules["fallback"]