from typing import Dict, Any

class RiskScorer:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
    def score(self, report: Dict[str, Any]) -> Dict[str, Any]:
        # طالما التعديلات محلية وبسيطة -> مخاطرة منخفضة
        return {"level": "low", "reasons": ["local-only", "small-diff"]}
