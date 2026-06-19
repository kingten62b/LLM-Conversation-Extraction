from dataclasses import dataclass, asdict

@dataclass
class ExtractionResult:
    conversation_id: str
    channel: str
    agent: str
    turn_count: int
    user_issue_summary: str
    issue_categories: list[str]
    resolution_status: str
    resolution_action: str
    user_sentiment: str
    urgency_level: str
    requires_follow_up: bool
    escalation_required: bool

    def to_dict(self):
        return asdict(self)
