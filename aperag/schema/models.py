from typing import Optional

from pydantic import BaseModel, conint


class LLMConfig(BaseModel):
    prompt_template: Optional[str] = None
    trial: Optional[bool] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    deployment_id: Optional[str] = None
    api_version: Optional[str] = None
    endpoint: Optional[str] = None
    token: Optional[str] = None
    secret_key: Optional[str] = None
    context_window: conint(ge=0, le=5120000)
    similarity_score_threshold: float
    similarity_topk: int
    temperature: float
    enable_keyword_recall: Optional[bool] = None
    related_prompt_template: Optional[str] = None


class BotConfig(BaseModel):
    model: str
    chractor: Optional[str] = None
    memory: Optional[bool] = None
    memory_length: Optional[int] = None
    memory_count: Optional[int] = None
    use_related_question: Optional[bool] = None
    related_question_prompt: Optional[str] = None
    llm: LLMConfig