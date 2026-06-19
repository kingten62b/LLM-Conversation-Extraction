import sys
from pathlib import Path

# Add project root to sys.path so imports work from any working directory
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.data import (
    load_conversations, load_results, save_results, compute_stats,
    save_uploaded_file, get_data_source,
)
from backend.extractor import extract_conversation, run_extraction

app = FastAPI(title="客服对话提取 API", description="基于 LangChain 的客服对话结构化提取服务")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 数据上传 ──

@app.get("/api/data-source")
def api_data_source():
    return get_data_source()


@app.post("/api/upload")
async def api_upload(file: UploadFile = File(...)):
    if not file.filename.endswith(".json"):
        raise HTTPException(400, "仅支持 JSON 文件")
    try:
        content = await file.read()
        result = save_uploaded_file(content)
        return {"status": "ok", **result}
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"上传失败: {str(e)}")


# ── 对话 ──

@app.get("/api/conversations")
def get_conversations(status: str = ""):
    convs = load_conversations()
    if status:
        results = load_results()
        done_ids = {r["conversation_id"] for r in results}
        if status == "done":
            convs = [c for c in convs if c["id"] in done_ids]
        elif status == "pending":
            convs = [c for c in convs if c["id"] not in done_ids]
    return {"total": len(convs), "conversations": convs}


@app.get("/api/conversations/{conv_id}")
def get_conversation(conv_id: str):
    convs = load_conversations()
    for c in convs:
        if c["id"] == conv_id:
            return c
    raise HTTPException(404, f"Conversation {conv_id} not found")


# ── 提取 ──

class ExtractRequest(BaseModel):
    conv_id: str


@app.post("/api/extract")
def extract_single(req: ExtractRequest):
    convs = load_conversations()
    for c in convs:
        if c["id"] == req.conv_id:
            result = extract_conversation(c)
            results = load_results()
            results = [r for r in results if r["conversation_id"] != req.conv_id]
            results.append(result)
            save_results(results)
            return result
    raise HTTPException(404, f"Conversation {req.conv_id} not found")


@app.post("/api/extract-all")
def extract_all():
    convs = load_conversations()
    results = run_extraction(convs)
    save_results(results)
    return {"total": len(results), "results": results}


# ── 结果 ──

@app.get("/api/results")
def get_results():
    return {"total": len(load_results()), "results": load_results()}


@app.get("/api/results/{conv_id}")
def get_result(conv_id: str):
    results = load_results()
    for r in results:
        if r["conversation_id"] == conv_id:
            return r
    raise HTTPException(404, f"Result for {conv_id} not found")


@app.get("/api/stats")
def get_stats():
    results = load_results()
    return compute_stats(results)


# ── 验证 ──

class ValidateRequest(BaseModel):
    conv_id: str
    field: str
    is_correct: bool


validations: list[dict] = []


@app.get("/api/validations")
def get_validations():
    return {"total": len(validations), "validations": validations}


@app.post("/api/validate")
def validate_field(req: ValidateRequest):
    results = load_results()
    for r in results:
        if r["conversation_id"] == req.conv_id:
            validations.append({
                "conversation_id": req.conv_id,
                "field": req.field,
                "is_correct": req.is_correct,
                "value": r.get(req.field),
            })
            return {"status": "ok"}
    raise HTTPException(404, f"Result for {req.conv_id} not found")


class BatchValidateRequest(BaseModel):
    validations: list[ValidateRequest]


@app.post("/api/validate/batch")
def validate_batch(req: BatchValidateRequest):
    results = load_results()
    result_map = {r["conversation_id"]: r for r in results}
    added = 0
    for v in req.validations:
        conv = result_map.get(v.conv_id)
        if conv is None:
            continue
        validations.append({
            "conversation_id": v.conv_id,
            "field": v.field,
            "is_correct": v.is_correct,
            "value": conv.get(v.field),
        })
        added += 1
    return {"status": "ok", "added": added}


@app.get("/api/validate/summary")
def validate_summary():
    if not validations:
        return {"total": 0, "accuracy": 0, "per_field": {}}
    total = len(validations)
    correct = sum(1 for v in validations if v["is_correct"])
    per_field: dict[str, dict] = {}
    for v in validations:
        f = v["field"]
        if f not in per_field:
            per_field[f] = {"total": 0, "correct": 0}
        per_field[f]["total"] += 1
        if v["is_correct"]:
            per_field[f]["correct"] += 1
    return {
        "total": total,
        "correct": correct,
        "accuracy": round(correct / total * 100, 1),
        "per_field": {k: f"{v['correct']}/{v['total']}" for k, v in per_field.items()},
    }


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
