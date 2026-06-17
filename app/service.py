from app.db import EvaluationDB
from app.models import EvaluationEntry, ExpertFeedback, RagasScores
from app.ragas_runner import RagasRunner


class EvaluationService:

    def __init__(self, db: EvaluationDB, ragas_runner: RagasRunner, logger_enabled: bool = True):
        self._db = db
        self._ragas = ragas_runner
        self._logger_enabled = logger_enabled

    def log_evaluation(
        self,
        question: str,
        sparql_query: str,
        triplets: list,
        generated_response: str,
        username: str = None,
        prompt_mode: str = None,
    ) -> str | None:
        if not self._logger_enabled:
            return None
        return self.create_evaluation(
            question=question,
            sparql_query=sparql_query,
            triplets=triplets,
            generated_response=generated_response,
            username=username,
            prompt_mode=prompt_mode,
        )

    def create_evaluation(
        self,
        question: str,
        sparql_query: str,
        triplets: list,
        generated_response: str,
        username: str = None,
        prompt_mode: str = None,
    ) -> str:
        entry = EvaluationEntry(
            question=question,
            sparql_query=sparql_query,
            retrieved_triplets=triplets,
            generated_response=generated_response,
            username=username,
            prompt_mode=prompt_mode,
        )
        return self._db.insert_evaluation(entry)

    def evaluate_both_modes(
        self,
        pipeline,
        question: str,
        username: str = None,
    ) -> dict:
        """Run the question through both modes, store both evals, return both answers."""
        results = {}
        for mode in ("technical", "friendly"):
            result = pipeline.query(question, mode=mode)
            eval_id = self.create_evaluation(
                question=question,
                sparql_query=result.get("sparql_query", ""),
                triplets=result.get("context", "").splitlines(),
                generated_response=result.get("answer", ""),
                username=username,
                prompt_mode=mode,
            )
            results[mode] = {"eval_id": eval_id, "answer": result.get("answer", "")}
        return results

    def submit_feedback(
        self,
        eval_id: str,
        rating: int,
        correction: str = None,
        issues: list = None,
        note: str = None,
    ) -> dict:
        if rating <= 2:
            status = "WRONG"
        elif rating == 3:
            status = "PARTIAL"
        else:
            status = "CORRECT"

        feedback = ExpertFeedback(
            expert_rating=rating,
            expert_status=status,
            expert_correction=correction,
            expert_issues=issues,
            expert_note=note,
        )
        self._db.update_expert_feedback(eval_id, feedback)
        return {"eval_id": eval_id, "expert_status": status}

    def run_ragas(self, eval_id: str) -> dict:
        row = self._db.get_evaluation(eval_id)
        if row is None:
            raise ValueError(f"Evaluation {eval_id} not found")

        reference = row.get("expert_correction") or None
        scores = self._ragas.run(
            question=row["question"],
            triplets=row.get("retrieved_triplets") or [],
            response=row.get("generated_response") or "",
            reference=reference,
        )
        self._db.update_ragas_scores(eval_id, scores)
        return {
            "eval_id": eval_id,
            "scores": {
                "faithfulness": scores.faithfulness,
                "context_recall": scores.context_recall,
                "context_precision": scores.context_precision,
                "factual_correctness": scores.factual_correctness,
                "semantic_similarity": scores.semantic_similarity,
            },
        }

    def get_stats(self, username: str = None) -> dict:
        rows = self._db.list_evaluations(username=username)
        total = len(rows)
        by_status = {"WRONG": 0, "PARTIAL": 0, "CORRECT": 0}

        ragas_fields = [
            "ragas_faithfulness",
            "ragas_context_recall",
            "ragas_context_precision",
            "ragas_factual_correctness",
            "ragas_semantic_similarity",
        ]
        sums = {f: 0.0 for f in ragas_fields}
        counts = {f: 0 for f in ragas_fields}

        for row in rows:
            status = row.get("expert_status")
            if status in by_status:
                by_status[status] += 1
            for f in ragas_fields:
                val = row.get(f)
                if val is not None:
                    sums[f] += val
                    counts[f] += 1

        key_map = {
            "ragas_faithfulness": "faithfulness",
            "ragas_context_recall": "context_recall",
            "ragas_context_precision": "context_precision",
            "ragas_factual_correctness": "factual_correctness",
            "ragas_semantic_similarity": "semantic_similarity",
        }
        avg_ragas = {
            label: round(sums[f] / counts[f], 4) if counts[f] > 0 else None
            for f, label in key_map.items()
        }

        return {"total": total, "by_status": by_status, "avg_ragas": avg_ragas}
