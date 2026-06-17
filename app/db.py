import json
import sqlite3
import uuid
from datetime import datetime, timezone

from app.models import EvaluationEntry, ExpertFeedback, RagasScores


class EvaluationDB:

    def __init__(self, db_path: str):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS evaluations (
                id                          TEXT PRIMARY KEY,
                timestamp                   TEXT NOT NULL,
                question                    TEXT NOT NULL,
                sparql_query                TEXT,
                retrieved_triplets          TEXT,
                generated_response          TEXT,
                username                    TEXT,
                expert_rating               INTEGER,
                expert_status               TEXT,
                expert_correction           TEXT,
                expert_issues               TEXT,
                expert_note                 TEXT,
                ragas_faithfulness          REAL,
                ragas_context_recall        REAL,
                ragas_context_precision     REAL,
                ragas_factual_correctness   REAL,
                ragas_semantic_similarity   REAL,
                prompt_mode                 TEXT
            )
        """)
        for col in ("username TEXT", "prompt_mode TEXT"):
            try:
                self._conn.execute(f"ALTER TABLE evaluations ADD COLUMN {col}")
            except Exception:
                pass
        self._conn.commit()

    def insert_evaluation(self, data: EvaluationEntry) -> str:
        eval_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """
            INSERT INTO evaluations
                (id, timestamp, question, sparql_query, retrieved_triplets, generated_response, username, prompt_mode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                eval_id,
                timestamp,
                data.question,
                data.sparql_query,
                json.dumps(data.retrieved_triplets, ensure_ascii=False),
                data.generated_response,
                data.username,
                data.prompt_mode,
            ),
        )
        self._conn.commit()
        return eval_id

    def update_expert_feedback(self, eval_id: str, feedback: ExpertFeedback):
        self._conn.execute(
            """
            UPDATE evaluations SET
                expert_rating     = ?,
                expert_status     = ?,
                expert_correction = ?,
                expert_issues     = ?,
                expert_note       = ?
            WHERE id = ?
            """,
            (
                feedback.expert_rating,
                feedback.expert_status,
                feedback.expert_correction,
                json.dumps(feedback.expert_issues, ensure_ascii=False) if feedback.expert_issues is not None else None,
                feedback.expert_note,
                eval_id,
            ),
        )
        self._conn.commit()

    def update_ragas_scores(self, eval_id: str, scores: RagasScores):
        self._conn.execute(
            """
            UPDATE evaluations SET
                ragas_faithfulness          = ?,
                ragas_context_recall        = ?,
                ragas_context_precision     = ?,
                ragas_factual_correctness   = ?,
                ragas_semantic_similarity   = ?
            WHERE id = ?
            """,
            (
                scores.faithfulness,
                scores.context_recall,
                scores.context_precision,
                scores.factual_correctness,
                scores.semantic_similarity,
                eval_id,
            ),
        )
        self._conn.commit()

    def get_evaluation(self, eval_id: str) -> dict:
        row = self._conn.execute(
            "SELECT * FROM evaluations WHERE id = ?", (eval_id,)
        ).fetchone()
        if row is None:
            return None
        return self._row_to_dict(row)

    def list_evaluations(self, status: str = None, username: str = None) -> list:
        conditions = []
        params = []

        if status:
            conditions.append("expert_status = ?")
            params.append(status)
        if username:
            conditions.append("username = ?")
            params.append(username)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        rows = self._conn.execute(
            f"SELECT * FROM evaluations {where} ORDER BY timestamp DESC",
            params,
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        d = {k: row[k] for k in row.keys()}
        for key in ("retrieved_triplets", "expert_issues"):
            if d.get(key) is not None:
                try:
                    d[key] = json.loads(d[key])
                except (json.JSONDecodeError, TypeError):
                    pass
        return d
