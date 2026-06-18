from typing import Literal
from pydantic import BaseModel, Field

ScorerType = Literal["exact", "contains", "regex", "llm-judge"]


class EvalCase(BaseModel):
    id: str
    prompt: str
    expected: str
    scorer: ScorerType
    rubric: str | None = None


class EvalSuite(BaseModel):
    suite: str
    cases: list[EvalCase] = Field(min_length=1)
