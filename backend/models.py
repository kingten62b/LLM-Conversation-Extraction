from pydantic import BaseModel
from typing import Optional


class ConversationTurn(BaseModel):
    role: str
    content: str


class Conversation(BaseModel):
    id: str
    channel: str
    agent: str
    turns: list[ConversationTurn]


class ExtractionResult(BaseModel):
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


class ValidationEntry(BaseModel):
    field: str
    is_correct: bool
