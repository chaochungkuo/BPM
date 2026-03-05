from __future__ import annotations

from dataclasses import dataclass

from bpm.core.agent_template_index import list_templates
from bpm.core.descriptor_loader import load as load_desc


@dataclass(frozen=True)
class Recommendation:
    template_id: str
    score: int
    reason: str
    source_path: str


def recommend(goal: str, top_k: int = 3) -> list[Recommendation]:
    q = (goal or "").strip().lower()
    tokens = [t for t in q.replace("_", " ").replace("-", " ").split() if t]

    recs: list[Recommendation] = []
    for entry in list_templates():
        try:
            desc = load_desc(entry.template_id)
            description = (desc.description or "").lower()
        except Exception:
            description = ""

        hay = f"{entry.template_id.lower()} {description}"
        score = 0
        for t in tokens:
            if t in hay:
                score += 1

        if not tokens:
            score = 1

        if score > 0:
            reason = "matched keywords in template id/description" if tokens else "default listing"
            recs.append(
                Recommendation(
                    template_id=entry.template_id,
                    score=score,
                    reason=reason,
                    source_path=str(entry.descriptor_path),
                )
            )

    recs.sort(key=lambda r: (-r.score, r.template_id))
    return recs[:top_k]
