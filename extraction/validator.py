import json, random

def validate_results(extraction_results: list[dict], sample_size: int = 7):
    """人工抽检验证准确率"""
    convs_raw = json.load(open("/home/tea/code/fastapi/code/0108/task2_conversations.json"))
    conv_map = {c["id"]: c for c in convs_raw}
    sampled = random.sample(extraction_results, min(sample_size, len(extraction_results)))
    
    fields = ["issue_categories", "resolution_status", "user_sentiment", "urgency_level", "requires_follow_up", "escalation_required"]
    
    total, correct = 0, 0
    per_field = {f: {"correct": 0, "total": 0} for f in fields}
    details = []
    
    print("=" * 60)
    print("人工抽检验证")
    print("=" * 60)
    print(f"抽检 {len(sampled)} 条对话")
    print()
    
    for r in sampled:
        cid = r["conversation_id"]
        conv = conv_map[cid]
        print(f"--- {cid} ---")
        print(f"  提取: categories={r['issue_categories']}, status={r['resolution_status']}, sentiment={r['user_sentiment']}")
        print(f"         urgency={r['urgency_level']}, follow_up={r['requires_follow_up']}, esc={r['escalation_required']}")
        print()
        
        record = {"id": cid}
        for f in fields:
            record[f] = input(f"  [{f}] = {r[f]} 是否正确? (y/n): ").strip().lower() == "y"
            total += 1
            per_field[f]["total"] += 1
            if record[f]:
                correct += 1
                per_field[f]["correct"] += 1
        details.append(record)
    
    accuracy = correct / total if total > 0 else 0
    print()
    print("=" * 60)
    print("准确率报告")
    print("=" * 60)
    print(f"抽检条数: {len(sampled)}")
    print(f"总字段数: {total}")
    print(f"正确数: {correct}")
    print(f"整体准确率: {accuracy:.1%}")
    print()
    print("各字段准确率:")
    for f in fields:
        pf = per_field[f]
        print(f"  {f}: {pf['correct']}/{pf['total']} = {pf['correct']/pf['total']:.0%}" if pf['total'] > 0 else f"  {f}: 0/0 = N/A")
    
    return {"accuracy": accuracy, "per_field": {f: f"{pf['correct']}/{pf['total']}" for f, pf in per_field.items()}}
