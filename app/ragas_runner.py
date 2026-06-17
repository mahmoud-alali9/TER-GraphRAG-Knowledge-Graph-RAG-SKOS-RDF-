from ragas import evaluate, EvaluationDataset, SingleTurnSample
from ragas.metrics import (
    Faithfulness,
    LLMContextRecall,
    LLMContextPrecisionWithoutReference,
    LLMContextPrecisionWithReference,
    FactualCorrectness,
    SemanticSimilarity,
)
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.models import RagasScores


class RagasRunner:

    def __init__(self, metrics: list, llm_model: str):
        llm = LangchainLLMWrapper(ChatOpenAI(model=llm_model, temperature=0))
        embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings())

        metric_map = {
            "faithfulness":        Faithfulness(llm=llm),
            "context_recall":      LLMContextRecall(llm=llm),
            "factual_correctness": FactualCorrectness(llm=llm),
            "semantic_similarity": SemanticSimilarity(embeddings=embeddings),
        }

        self._metrics = []
        self._needs_reference = False
        for name in metrics:
            if name == "context_precision":
                # resolved at run-time based on whether a reference exists
                self._has_context_precision = True
                self._llm = llm
            elif name in metric_map:
                self._metrics.append(metric_map[name])

        if not hasattr(self, "_has_context_precision"):
            self._has_context_precision = False

        if any(isinstance(m, (LLMContextRecall, FactualCorrectness, SemanticSimilarity)) for m in self._metrics):
            self._needs_reference = True

    def run(
        self,
        question : str,
        triplets : list,
        response : str,
        reference: str = None,
    ) -> RagasScores:
        contexts = [str(t) for t in triplets] if triplets else [""]

        # Pick context_precision variant based on whether we have a reference
        active_metrics = list(self._metrics)
        if self._has_context_precision:
            if reference:
                active_metrics.append(LLMContextPrecisionWithReference(llm=self._llm))
            else:
                active_metrics.append(LLMContextPrecisionWithoutReference(llm=self._llm))

        sample = SingleTurnSample(
            user_input=question,
            retrieved_contexts=contexts,
            response=response,
            reference=reference,
        )

        dataset = EvaluationDataset(samples=[sample])
        result = evaluate(dataset=dataset, metrics=active_metrics)

        scores_row = result.to_pandas().iloc[0].to_dict()

        def _get(key):
            val = scores_row.get(key)
            return float(val) if val is not None else None

        # LLMContextPrecisionWithReference and WithoutReference both produce
        # a column named "llm_context_precision_with_reference" or
        # "llm_context_precision_without_reference" — normalise to one key.
        context_precision = (
            _get("llm_context_precision_with_reference")
            or _get("llm_context_precision_without_reference")
        )

        return RagasScores(
            faithfulness        = _get("faithfulness"),
            context_recall      = _get("llm_context_recall"),
            context_precision   = context_precision,
            factual_correctness = _get("factual_correctness"),
            semantic_similarity = _get("semantic_similarity"),
        )
