import asyncio
import uuid
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

from workflow.prompts import MODES, DEFAULT_MODE

router = APIRouter()

# ── In-memory admin state (cleared on restart) ─────────────────────────────────
_admin_sessions: set[str] = set()
_ragas_jobs: dict[str, dict] = {}


# ── Request models ─────────────────────────────────────────────────────────────

class MessageRequest(BaseModel):
    message : str
    mode    : str = DEFAULT_MODE
    username: str | None = None


class FeedbackEvalRequest(BaseModel):
    expert_rating    : int = Field(ge=1, le=5)
    expert_correction: str | None = None
    expert_issues    : list | None = None
    expert_note      : str | None = None


class CreateEvaluationRequest(BaseModel):
    question          : str
    sparql_query      : str = ""
    retrieved_triplets: list = []
    generated_response: str = ""
    prompt_mode       : str | None = None
    username          : str | None = None


class AdminLoginRequest(BaseModel):
    password: str


class RagasRunRequest(BaseModel):
    scope: str = "pending_ragas"  # "pending_ragas" | "all"


# ── Helpers ────────────────────────────────────────────────────────────────────

def _state(request: Request):
    return request.app.state


def _triplets_from_context(context: str) -> list:
    return [t for t in (context or "").split("\n\n") if t.strip()]


def _require_admin(request: Request, authorization: str | None):
    token = (authorization or "").removeprefix("Bearer ").strip()
    if not token or token not in _admin_sessions:
        raise HTTPException(status_code=401, detail="Admin authentication required.")


# ── Pipeline routes ────────────────────────────────────────────────────────────

@router.get("/")
def root():
    return {"status": "Forest GraphRAG API is running.", "docs": "/docs"}


@router.post("/message")
def post_message(payload: MessageRequest, request: Request):
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="`message` must not be empty.")
    if payload.mode not in MODES:
        raise HTTPException(status_code=400, detail=f"`mode` must be one of {list(MODES)}.")

    state = _state(request)
    result = state.pipeline.query(message, mode=payload.mode)
    triplets = _triplets_from_context(result.get("context", ""))

    eval_id = state.eval_service.log_evaluation(
        question=result["question"],
        sparql_query=result.get("sparql_query", ""),
        triplets=triplets,
        generated_response=result["answer"],
        prompt_mode=payload.mode,
        username=payload.username,
    )
    return {
        "eval_id"    : eval_id,
        "question"   : result["question"],
        "intent"     : result["intent"],
        "answer"     : result["answer"],
        "mode"       : payload.mode,
        "output_file": result["output_path"],
    }


@router.post("/message/both-modes")
def post_message_both_modes(payload: MessageRequest, request: Request):
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="`message` must not be empty.")

    state = _state(request)
    results = state.eval_service.evaluate_both_modes(
        state.pipeline, message, username=payload.username
    )
    return results


# ── Evaluation routes ──────────────────────────────────────────────────────────

@router.post("/evaluations", status_code=201)
def post_evaluation(payload: CreateEvaluationRequest, request: Request):
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="`question` must not be empty.")

    state = _state(request)
    eval_id = state.eval_service.create_evaluation(
        question=question,
        sparql_query=payload.sparql_query,
        triplets=payload.retrieved_triplets,
        generated_response=payload.generated_response,
        prompt_mode=payload.prompt_mode,
        username=payload.username,
    )
    row = state.eval_service._db.get_evaluation(eval_id)
    return {"eval_id": eval_id, "timestamp": row["timestamp"], "status": "pending"}


@router.patch("/evaluations/{eval_id}/feedback")
def patch_feedback(eval_id: str, payload: FeedbackEvalRequest, request: Request):
    state = _state(request)
    if state.eval_service._db.get_evaluation(eval_id) is None:
        raise HTTPException(status_code=404, detail=f"Evaluation {eval_id} not found.")
    return state.eval_service.submit_feedback(
        eval_id=eval_id,
        rating=payload.expert_rating,
        correction=payload.expert_correction,
        issues=payload.expert_issues,
        note=payload.expert_note,
    )


@router.post("/evaluations/{eval_id}/ragas")
def post_ragas(eval_id: str, request: Request):
    state = _state(request)
    if state.eval_service._db.get_evaluation(eval_id) is None:
        raise HTTPException(status_code=404, detail=f"Evaluation {eval_id} not found.")
    try:
        return state.eval_service.run_ragas(eval_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/evaluations")
def get_evaluations(request: Request, status: str | None = None, username: str | None = None):
    allowed = {"WRONG", "PARTIAL", "CORRECT"}
    if status is not None and status not in allowed:
        raise HTTPException(status_code=400, detail=f"`status` must be one of {sorted(allowed)}.")
    rows = _state(request).eval_service._db.list_evaluations(status=status, username=username)
    return [
        {
            "eval_id"      : r["id"],
            "question"     : r["question"],
            "expert_status": r.get("expert_status"),
            "prompt_mode"  : r.get("prompt_mode"),
            "timestamp"    : r["timestamp"],
        }
        for r in rows
    ]


@router.get("/evaluations/{eval_id}")
def get_evaluation(eval_id: str, request: Request):
    row = _state(request).eval_service._db.get_evaluation(eval_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Evaluation {eval_id} not found.")
    return {
        "id"                : row["id"],
        "question"          : row["question"],
        "prompt_mode"       : row.get("prompt_mode"),
        "sparql_query"      : row.get("sparql_query"),
        "retrieved_triplets": row.get("retrieved_triplets"),
        "generated_response": row.get("generated_response"),
        "expert_rating"     : row.get("expert_rating"),
        "expert_status"     : row.get("expert_status"),
        "expert_correction" : row.get("expert_correction"),
        "expert_issues"     : row.get("expert_issues"),
        "expert_note"       : row.get("expert_note"),
        "ragas_scores": {
            "faithfulness"       : row.get("ragas_faithfulness"),
            "context_recall"     : row.get("ragas_context_recall"),
            "context_precision"  : row.get("ragas_context_precision"),
            "factual_correctness": row.get("ragas_factual_correctness"),
            "semantic_similarity": row.get("ragas_semantic_similarity"),
        },
    }


@router.get("/stats")
def get_stats(request: Request, username: str | None = None):
    return _state(request).eval_service.get_stats(username=username)


@router.get("/historique")
def get_historique(request: Request, username: str | None = None):
    rows = _state(request).eval_service._db.list_evaluations(username=username)
    return [
        {
            "eval_id"  : r["id"],
            "question" : r["question"],
            "answer"   : r.get("generated_response") or "",
            "intent"   : "",
            "mode"     : r.get("prompt_mode") or DEFAULT_MODE,
            "timestamp": r["timestamp"],
        }
        for r in rows
    ]


# ── Admin auth ─────────────────────────────────────────────────────────────────

@router.post("/admin/login")
def admin_login(payload: AdminLoginRequest, request: Request):
    expected = _state(request).admin_password
    if not expected or payload.password != expected:
        raise HTTPException(status_code=401, detail="Invalid password.")
    token = str(uuid.uuid4())
    _admin_sessions.add(token)
    return {"token": token}


@router.post("/admin/logout")
def admin_logout(authorization: Annotated[str | None, Header()] = None):
    token = (authorization or "").removeprefix("Bearer ").strip()
    _admin_sessions.discard(token)
    return {"status": "logged out"}


# ── Admin evaluation routes ────────────────────────────────────────────────────

@router.get("/admin/evaluations")
def admin_get_evaluations(
    request: Request,
    status: str | None = None,
    authorization: Annotated[str | None, Header()] = None,
):
    _require_admin(request, authorization)
    allowed = {"WRONG", "PARTIAL", "CORRECT"}
    if status is not None and status not in allowed:
        raise HTTPException(status_code=400, detail=f"`status` must be one of {sorted(allowed)}.")
    rows = _state(request).eval_service._db.list_evaluations(status=status)
    return [
        {
            "eval_id"      : r["id"],
            "question"     : r["question"],
            "username"     : r.get("username"),
            "expert_status": r.get("expert_status"),
            "prompt_mode"  : r.get("prompt_mode"),
            "timestamp"    : r["timestamp"],
        }
        for r in rows
    ]


@router.get("/admin/evaluations/{eval_id}")
def admin_get_evaluation(
    eval_id: str,
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
):
    _require_admin(request, authorization)
    row = _state(request).eval_service._db.get_evaluation(eval_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Evaluation {eval_id} not found.")
    return {
        "id"                : row["id"],
        "question"          : row["question"],
        "username"          : row.get("username"),
        "prompt_mode"       : row.get("prompt_mode"),
        "sparql_query"      : row.get("sparql_query"),
        "retrieved_triplets": row.get("retrieved_triplets"),
        "generated_response": row.get("generated_response"),
        "expert_rating"     : row.get("expert_rating"),
        "expert_status"     : row.get("expert_status"),
        "expert_correction" : row.get("expert_correction"),
        "expert_issues"     : row.get("expert_issues"),
        "expert_note"       : row.get("expert_note"),
        "timestamp"         : row["timestamp"],
        "ragas_scores": {
            "faithfulness"       : row.get("ragas_faithfulness"),
            "context_recall"     : row.get("ragas_context_recall"),
            "context_precision"  : row.get("ragas_context_precision"),
            "factual_correctness": row.get("ragas_factual_correctness"),
            "semantic_similarity": row.get("ragas_semantic_similarity"),
        },
    }


@router.get("/admin/stats")
def admin_get_stats(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
):
    _require_admin(request, authorization)
    return _state(request).eval_service.get_stats()


@router.get("/admin/users")
def admin_get_users(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
):
    _require_admin(request, authorization)
    rows = _state(request).eval_service._db.list_evaluations()
    counts: dict[str, int] = {}
    for r in rows:
        u = r.get("username") or "anonyme"
        counts[u] = counts.get(u, 0) + 1
    return [{"username": u, "total": counts[u]} for u in sorted(counts)]


# ── Admin RAGAS batch ──────────────────────────────────────────────────────────

def _execute_ragas_job(job_id: str, eval_ids: list, eval_service):
    job = _ragas_jobs[job_id]
    job["status"] = "running"
    for eval_id in eval_ids:
        try:
            eval_service.run_ragas(eval_id)
        except Exception as exc:
            job["errors"].append(f"{eval_id}: {str(exc)[:120]}")
        finally:
            job["processed"] += 1
    job["status"] = "done"


@router.post("/admin/ragas/run")
async def admin_ragas_run(
    payload: RagasRunRequest,
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
):
    _require_admin(request, authorization)
    state = _state(request)
    rows = state.eval_service._db.list_evaluations()

    if payload.scope == "pending_ragas":
        targets = [r["id"] for r in rows if r.get("ragas_faithfulness") is None]
    else:
        targets = [r["id"] for r in rows]

    if not targets:
        return {"job_id": None, "total": 0, "message": "No evaluations to process."}

    job_id = str(uuid.uuid4())
    _ragas_jobs[job_id] = {"status": "queued", "total": len(targets), "processed": 0, "errors": []}

    loop = asyncio.get_running_loop()
    loop.run_in_executor(
        state.ragas_executor,
        _execute_ragas_job,
        job_id,
        targets,
        state.eval_service,
    )
    return {"job_id": job_id, "total": len(targets)}


@router.get("/admin/ragas/job/{job_id}")
def admin_ragas_job_status(
    job_id: str,
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
):
    _require_admin(request, authorization)
    job = _ragas_jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return {"job_id": job_id, **job}
