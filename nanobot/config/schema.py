"""模块说明：schema。"""

from pathlib import Path
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class WhatsAppConfig(BaseModel):
    """类说明：WhatsAppConfig。"""
    enabled: bool = False
    bridge_url: str = "ws://localhost:3001"
    allow_from: list[str] = Field(default_factory=list)  # 允许的手机号


class TelegramConfig(BaseModel):
    """类说明：TelegramConfig。"""
    enabled: bool = False
    token: str = ""  # 来自 @BotFather 的机器人令牌
    allow_from: list[str] = Field(default_factory=list)  # 允许的用户 ID 或用户名
    proxy: str | None = None  # HTTP/SOCKS5 代理 URL，例如 "http://127.0.0.1:7890" 或 "socks5://127.0.0.1:1080"


class FeishuConfig(BaseModel):
    """类说明：FeishuConfig。"""
    enabled: bool = False
    app_id: str = ""  # 来自飞书开放平台的 App ID
    app_secret: str = ""  # 来自飞书开放平台的 App Secret
    encrypt_key: str = ""  # 事件订阅的 Encrypt Key（可选）
    verification_token: str = ""  # 事件订阅的 Verification Token（可选）
    allow_from: list[str] = Field(default_factory=list)  # 允许的用户 open_id


class DiscordConfig(BaseModel):
    """类说明：DiscordConfig。"""
    enabled: bool = False
    token: str = ""  # 来自 Discord 开发者平台的机器人令牌
    allow_from: list[str] = Field(default_factory=list)  # 允许的用户 ID
    gateway_url: str = "wss://gateway.discord.gg/?v=10&encoding=json"
    intents: int = 37377  # 需要的 intents：GUILDS + GUILD_MESSAGES + DIRECT_MESSAGES + MESSAGE_CONTENT


class ChannelsConfig(BaseModel):
    """类说明：ChannelsConfig。"""
    whatsapp: WhatsAppConfig = Field(default_factory=WhatsAppConfig)
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    discord: DiscordConfig = Field(default_factory=DiscordConfig)
    feishu: FeishuConfig = Field(default_factory=FeishuConfig)


class AgentDefaults(BaseModel):
    """类说明：AgentDefaults。"""
    workspace: str = "~/.nanobot/workspace"
    model: str = "anthropic/claude-opus-4-5"
    max_tokens: int = 8192
    temperature: float = 0.7
    max_tool_iterations: int = 20


class AgentsConfig(BaseModel):
    """类说明：AgentsConfig。"""
    defaults: AgentDefaults = Field(default_factory=AgentDefaults)


class ProviderConfig(BaseModel):
    """类说明：ProviderConfig。"""
    api_key: str = ""
    api_base: str | None = None


class ProvidersConfig(BaseModel):
    """类说明：ProvidersConfig。"""
    anthropic: ProviderConfig = Field(default_factory=ProviderConfig)
    openai: ProviderConfig = Field(default_factory=ProviderConfig)
    openrouter: ProviderConfig = Field(default_factory=ProviderConfig)
    deepseek: ProviderConfig = Field(default_factory=ProviderConfig)
    groq: ProviderConfig = Field(default_factory=ProviderConfig)
    zhipu: ProviderConfig = Field(default_factory=ProviderConfig)
    vllm: ProviderConfig = Field(default_factory=ProviderConfig)
    gemini: ProviderConfig = Field(default_factory=ProviderConfig)
    moonshot: ProviderConfig = Field(default_factory=ProviderConfig)


class GatewayConfig(BaseModel):
    """类说明：GatewayConfig。"""
    host: str = "0.0.0.0"
    port: int = 18790


class WebSearchConfig(BaseModel):
    """类说明：WebSearchConfig。"""
    api_key: str = ""  # Brave Search API 密钥
    max_results: int = 5


class WebToolsConfig(BaseModel):
    """类说明：WebToolsConfig。"""
    search: WebSearchConfig = Field(default_factory=WebSearchConfig)


class ExecToolConfig(BaseModel):
    """类说明：ExecToolConfig。"""
    timeout: int = 60


class ToolsConfig(BaseModel):
    """类说明：ToolsConfig。"""
    web: WebToolsConfig = Field(default_factory=WebToolsConfig)
    exec: ExecToolConfig = Field(default_factory=ExecToolConfig)
    restrict_to_workspace: bool = False  # 为 true 时，将所有工具访问限制在工作区目录


class Config(BaseSettings):
    """类说明：Config。"""
    agents: AgentsConfig = Field(default_factory=AgentsConfig)
    channels: ChannelsConfig = Field(default_factory=ChannelsConfig)
    providers: ProvidersConfig = Field(default_factory=ProvidersConfig)
    gateway: GatewayConfig = Field(default_factory=GatewayConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    
    @property
    def workspace_path(self) -> Path:
        """函数说明：workspace_path。"""
        return Path(self.agents.defaults.workspace).expanduser()
    
    def _match_provider(self, model: str | None = None) -> ProviderConfig | None:
        """函数说明：_match_provider。"""
        model = (model or self.agents.defaults.model).lower()
        # 中文注释
        providers = {
            "openrouter": self.providers.openrouter,
            "deepseek": self.providers.deepseek,
            "anthropic": self.providers.anthropic,
            "claude": self.providers.anthropic,
            "openai": self.providers.openai,
            "gpt": self.providers.openai,
            "gemini": self.providers.gemini,
            "zhipu": self.providers.zhipu,
            "glm": self.providers.zhipu,
            "zai": self.providers.zhipu,
            "groq": self.providers.groq,
            "moonshot": self.providers.moonshot,
            "kimi": self.providers.moonshot,
            "vllm": self.providers.vllm,
        }
        for keyword, provider in providers.items():
            if keyword in model and provider.api_key:
                return provider
        return None

    def get_api_key(self, model: str | None = None) -> str | None:
        """函数说明：get_api_key。"""
        # 中文注释
        matched = self._match_provider(model)
        if matched:
            return matched.api_key
        # 中文注释
        for provider in [
            self.providers.openrouter, self.providers.deepseek,
            self.providers.anthropic, self.providers.openai,
            self.providers.gemini, self.providers.zhipu,
            self.providers.moonshot, self.providers.vllm,
            self.providers.groq,
        ]:
            if provider.api_key:
                return provider.api_key
        return None
    
    def get_api_base(self, model: str | None = None) -> str | None:
        """函数说明：get_api_base。"""
        model = (model or self.agents.defaults.model).lower()
        if "openrouter" in model:
            return self.providers.openrouter.api_base or "https://openrouter.ai/api/v1"
        if any(k in model for k in ("zhipu", "glm", "zai")):
            return self.providers.zhipu.api_base
        if "vllm" in model:
            return self.providers.vllm.api_base
        if "openai" in model or "gpt" in model:
            return self.providers.openai.api_base
        return None
    
    class Config:
        env_prefix = "NANOBOT_"
        env_nested_delimiter = "__"
