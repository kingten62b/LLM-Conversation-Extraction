import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

load_dotenv()

API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

SYSTEM_PROMPT = """你是一个专业的客服对话分析助手。从客服对话中提取结构化信息，帮助客服主管进行周报统计。

提取以下字段，以JSON格式输出，不要包含其他文字：

1. user_issue_summary (str): 一句话概括用户的核心诉求，多诉求用分号分隔
2. issue_categories (list[str]): 问题类别列表，从以下选择（可多选）：
   商品质量问题、物流配送问题、退款/退货/换货、订单操作、产品咨询、优惠券/促销、账号安全、投诉/建议、其他
3. resolution_status (str): resolved(已解决) / partially_resolved(部分解决) / unresolved(未解决) / pending(待处理)
4. resolution_action (str): 客服采取的具体措施，如"发起退款"、"安排换新"
5. user_sentiment (str): angry(愤怒) / negative(负面) / neutral(中性) / positive(积极)
6. urgency_level (str): high(高) / medium(中) / low(低)
7. requires_follow_up (bool): 是否需要后续跟进
8. escalation_required (bool): 是否转人工处理"""


def create_chain():
    llm = ChatOpenAI(
        model=MODEL,
        api_key=API_KEY,
        base_url=BASE_URL,
        temperature=0.01,
        model_kwargs={"response_format": {"type": "json_object"}},
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "对话ID: {conv_id}\n渠道: {channel}\n客服: {agent}\n轮次: {turn_count}\n\n内容:\n{content}"),
    ])
    chain = prompt | llm | JsonOutputParser()
    return chain


def extract_conversation(conv: dict) -> dict:
    turns = conv.get("turns", [])
    lines = [f"{'用户' if t['role']=='user' else '客服'}: {t['content']}" for t in turns]
    content = "\n".join(lines)

    chain = create_chain()
    try:
        result = chain.invoke({
            "conv_id": conv["id"],
            "channel": conv["channel"],
            "agent": conv["agent"],
            "turn_count": len(turns),
            "content": content,
        })
        return {
            "conversation_id": conv["id"],
            "channel": conv["channel"],
            "agent": conv["agent"],
            "turn_count": len(turns),
            "user_issue_summary": result.get("user_issue_summary", ""),
            "issue_categories": result.get("issue_categories", ["其他"]),
            "resolution_status": result.get("resolution_status", "pending"),
            "resolution_action": result.get("resolution_action", ""),
            "user_sentiment": result.get("user_sentiment", "neutral"),
            "urgency_level": result.get("urgency_level", "medium"),
            "requires_follow_up": result.get("requires_follow_up", False),
            "escalation_required": result.get("escalation_required", False),
        }
    except Exception as e:
        print(f"  ERROR on {conv['id']}: {e}")
        return fallback_extract(conv)


def fallback_extract(conv: dict) -> dict:
    turns = conv.get("turns", [])
    text = " ".join(t["content"] for t in turns if t["role"] == "user")
    cats = []
    for kws, cat in [
        (["退款", "退货", "换货", "运费"], "退款/退货/换货"),
        (["快递", "收到", "配送", "签收", "快递柜"], "物流配送问题"),
        (["坏了", "碎了", "坏的", "不工作", "质量", "破损"], "商品质量问题"),
        (["优惠券", "促销", "满减"], "优惠券/促销"),
        (["账号", "密码", "登录", "安全"], "账号安全"),
        (["建议", "能不能", "反馈"], "投诉/建议"),
        (["查", "看看", "哪个好", "能带上", "成分", "补货"], "产品咨询"),
    ]:
        if any(k in text for k in kws):
            cats.append(cat)
    if not cats:
        cats.append("其他")
    return {
        "conversation_id": conv["id"],
        "channel": conv["channel"],
        "agent": conv["agent"],
        "turn_count": len(turns),
        "user_issue_summary": text[:80],
        "issue_categories": cats,
        "resolution_status": "pending",
        "resolution_action": "待识别",
        "user_sentiment": "neutral",
        "urgency_level": "medium",
        "requires_follow_up": True,
        "escalation_required": False,
    }


def run_extraction(conversations: list[dict]) -> list[dict]:
    results = []
    for i, conv in enumerate(conversations):
        cid = conv["id"]
        print(f"  [{i+1}/{len(conversations)}] {cid}...", end=" ", flush=True)
        r = extract_conversation(conv)
        results.append(r)
        print(f"OK | {r['resolution_status']} | {r['user_sentiment']}")
    return results
