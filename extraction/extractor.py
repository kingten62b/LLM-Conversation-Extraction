import os
import json
import time
import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

SYSTEM_PROMPT = (
    "你是一个专业的客服对话分析助手。从客服对话中提取结构化信息，帮助客服主管进行周报统计。\n\n"
    "提取以下字段，以JSON格式输出，不要包含其他文字：\n\n"
    "1. user_issue_summary (str): 一句话概括用户的核心诉求，多诉求用分号分隔\n"
    "2. issue_categories (list[str]): 问题类别列表，从以下选择（可多选）："
    "商品质量问题、物流配送问题、退款/退货/换货、订单操作、产品咨询、优惠券/促销、账号安全、投诉/建议、其他\n"
    "3. resolution_status (str): resolved(已解决) / partially_resolved(部分解决) / unresolved(未解决) / pending(待处理)\n"
    "4. resolution_action (str): 客服采取的具体措施，如「发起退款」「安排换新」\n"
    "5. user_sentiment (str): angry(愤怒) / negative(负面) / neutral(中性) / positive(积极)\n"
    "6. urgency_level (str): high(高) / medium(中) / low(低)\n"
    "7. requires_follow_up (bool): 是否需要后续跟进\n"
    "8. escalation_required (bool): 是否转人工处理"
)


def extract_conversation(conv: dict) -> dict:
    turns = conv.get("turns", [])
    lines = []
    for t in turns:
        role = "用户" if t["role"] == "user" else "客服"
        lines.append(f"{role}: {t['content']}")
    turn_text = "\n".join(lines)

    prompt = (
        f"对话ID: {conv['id']}\n"
        f"渠道: {conv['channel']}\n"
        f"客服: {conv['agent']}\n"
        f"轮次: {len(turns)}\n\n"
        f"内容:\n{turn_text}"
    )

    try:
        with httpx.Client(timeout=60) as client:
            resp = client.post(
                f"{BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.01,
                    "response_format": {"type": "json_object"},
                },
            )
            resp.raise_for_status()
            parsed = json.loads(resp.json()["choices"][0]["message"]["content"])
            return {
                "conversation_id": conv["id"],
                "channel": conv["channel"],
                "agent": conv["agent"],
                "turn_count": len(turns),
                "user_issue_summary": parsed.get("user_issue_summary", ""),
                "issue_categories": parsed.get("issue_categories", ["其他"]),
                "resolution_status": parsed.get("resolution_status", "pending"),
                "resolution_action": parsed.get("resolution_action", ""),
                "user_sentiment": parsed.get("user_sentiment", "neutral"),
                "urgency_level": parsed.get("urgency_level", "medium"),
                "requires_follow_up": parsed.get("requires_follow_up", False),
                "escalation_required": parsed.get("escalation_required", False),
            }
    except Exception as e:
        print(f"  ERROR: {e}")
        return fallback_extract(conv)


def fallback_extract(conv: dict) -> dict:
    turns = conv.get("turns", [])
    text = " ".join(t["content"] for t in turns if t["role"] == "user")
    cats = []

    rules = [
        (["退款", "退货", "换货", "运费"], "退款/退货/换货"),
        (["快递", "收到", "配送", "签收", "快递柜"], "物流配送问题"),
        (["坏了", "碎了", "坏的", "不工作", "质量", "破损"], "商品质量问题"),
        (["优惠券", "促销", "满减"], "优惠券/促销"),
        (["账号", "密码", "登录", "安全"], "账号安全"),
        (["建议", "能不能", "反馈"], "投诉/建议"),
        (["查", "看看", "哪个好", "能带上", "成分", "补货"], "产品咨询"),
    ]
    for kws, cat in rules:
        if any(k in text for k in kws):
            cats.append(cat)
    if not cats:
        cats.append("其他")

    sentiment = "neutral"
    if any(k in text for k in ["智障", "破服务", "投诉", "等了半天"]):
        sentiment = "angry"
    elif any(k in text for k in ["不满", "怕", "担心", "失望", "没信心"]):
        sentiment = "negative"
    elif "谢谢" in text:
        sentiment = "positive"

    return {
        "conversation_id": conv["id"],
        "channel": conv["channel"],
        "agent": conv["agent"],
        "turn_count": len(turns),
        "user_issue_summary": text[:80],
        "issue_categories": cats,
        "resolution_status": "pending",
        "resolution_action": "待识别",
        "user_sentiment": sentiment,
        "urgency_level": "medium",
        "requires_follow_up": True,
        "escalation_required": False,
    }


def run_extraction(conversations: list[dict]) -> list[dict]:
    results = []
    total = len(conversations)
    for i, conv in enumerate(conversations):
        cid = conv["id"]
        print(f"[{i+1}/{total}] {cid}...", end=" ", flush=True)
        r = extract_conversation(conv)
        results.append(r)
        cats = ", ".join(r.get("issue_categories", []))
        status = "OK" if r.get("issue_categories") else "FALLBACK"
        print(f"{status} | {r['resolution_status']} | {r['user_sentiment']} | {cats}")
        if i < total - 1:
            time.sleep(0.5)
    return results
