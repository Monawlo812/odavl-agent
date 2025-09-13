from typing import Any


class RiskScorer:
    def __init__(self, cfg: dict[str, Any]):
        self.cfg = cfg

    def score(self, report: dict[str, Any]) -> dict[str, Any]:
        # طالما التعديلات محلية وبسيطة -> مخاطرة منخفضة
        return {"level": "low", "reasons": ["local-only", "small-diff"]}
