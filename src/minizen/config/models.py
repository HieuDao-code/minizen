from pydantic import BaseModel


class MinifluxConfig(BaseModel):
    url: str
    api_key: str


class EmailConfig(BaseModel):
    smtp_host: str
    smtp_port: int
    from_addr: str
    to_addr: str
    username: str
    password: str


class AIConfig(BaseModel):
    model: str = "anthropic:claude-sonnet-4-6"
    top_n: int = 5


class Settings(BaseModel):
    miniflux: MinifluxConfig
    email: EmailConfig
    ai: AIConfig
