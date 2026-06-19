import json
import os

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "upload")
UPLOAD_FILE = os.path.join(UPLOAD_DIR, "conversations.json")
DEFAULT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "task2_conversations.json")
RESULTS_FILE = os.path.join(os.path.dirname(__file__), "..", "output", "extraction_results.json")


def load_conversations() -> list[dict]:
    """加载对话数据，优先使用上传的文件，否则使用默认数据文件"""
    path = UPLOAD_FILE if os.path.exists(UPLOAD_FILE) else DEFAULT_FILE
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_data_source() -> dict:
    """返回当前数据来源信息"""
    if os.path.exists(UPLOAD_FILE):
        return {"source": "upload", "path": UPLOAD_FILE}
    return {"source": "default", "path": DEFAULT_FILE}


def save_uploaded_file(content: bytes) -> dict:
    """保存上传的对话数据文件，返回保存结果"""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    data = json.loads(content.decode("utf-8"))
    if not isinstance(data, list):
        raise ValueError("JSON 数据必须是数组格式")
    if len(data) == 0:
        raise ValueError("JSON 数组不能为空")
    for i, item in enumerate(data):
        if "id" not in item or "turns" not in item:
            raise ValueError(f"第 {i+1} 条数据缺少必要字段 (id, turns)")
    with open(UPLOAD_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return {"conversations": len(data), "path": UPLOAD_FILE}


def load_results() -> list[dict]:
    path = os.path.abspath(RESULTS_FILE)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_results(results: list[dict]):
    path = os.path.abspath(RESULTS_FILE)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def compute_stats(results: list[dict]) -> dict:
    if not results:
        return {}
    cat_count: dict[str, int] = {}
    status_count: dict[str, int] = {}
    sentiment_count: dict[str, int] = {}
    urgency_count: dict[str, int] = {}

    for r in results:
        for cat in r.get("issue_categories", []):
            cat_count[cat] = cat_count.get(cat, 0) + 1
        s = r.get("resolution_status", "unknown")
        status_count[s] = status_count.get(s, 0) + 1
        se = r.get("user_sentiment", "unknown")
        sentiment_count[se] = sentiment_count.get(se, 0) + 1
        u = r.get("urgency_level", "unknown")
        urgency_count[u] = urgency_count.get(u, 0) + 1

    total = len(results)
    resolved = sum(1 for r in results if r.get("resolution_status") == "resolved")

    return {
        "total_conversations": total,
        "resolved_count": resolved,
        "resolution_rate": round(resolved / total * 100, 1) if total else 0,
        "issue_categories": dict(sorted(cat_count.items(), key=lambda x: -x[1])),
        "resolution_status": status_count,
        "user_sentiment": sentiment_count,
        "urgency_level": urgency_count,
    }
