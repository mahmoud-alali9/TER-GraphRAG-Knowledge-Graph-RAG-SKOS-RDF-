from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EvaluationEntry:
    question           : str
    sparql_query       : str
    retrieved_triplets : list
    generated_response : str
    username           : Optional[str] = None
    prompt_mode        : Optional[str] = None  # "technical" or "friendly"


@dataclass
class ExpertFeedback:
    expert_rating     : int
    expert_status     : str
    expert_correction : Optional[str] = None
    expert_issues     : Optional[list] = None
    expert_note       : Optional[str] = None


@dataclass
class RagasScores:
    faithfulness        : Optional[float] = None
    context_recall      : Optional[float] = None
    context_precision   : Optional[float] = None
    factual_correctness : Optional[float] = None
    semantic_similarity : Optional[float] = None
