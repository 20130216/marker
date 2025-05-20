import os
import torch
from typing import Optional
from dotenv import load_dotenv
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings
from enum import Enum

# ==================== 基础配置 ====================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class LLMServiceType(str, Enum):
    OPENAI = "marker.services.openai.OpenAIService"

# ==================== 加载环境变量 ====================
def load_environment_variables():
    # 确保 .env 路径绝对正确
    env_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "local.env"))
    print(f"🔍 正在加载环境文件: {env_path}")
    
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
        print("✅ 成功加载的环境变量:")
        print(f"OPENAI_MODEL={os.getenv('OPENAI_MODEL')}")
        print(f"OPENAI_API_KEY={os.getenv('OPENAI_API_KEY')}")
        print(f"OUTPUT_FORMAT={os.getenv('OUTPUT_FORMAT')}\n")
    else:
        raise FileNotFoundError(f"❌ 环境文件不存在: {env_path}")

# ==================== 主配置类 ====================
class Settings(BaseSettings):
    # ----- 设置这个重要的控制枢纽：USE_LLM；默认不用 LLM，只有明确写 True 才用 -----    
    USE_LLM: bool = Field(
    default=False,
    description="是否启用大模型（LLM）",
    env="USE_LLM"
    )
    
    # ----- 核心服务配置 -----
    LLM_SERVICE: LLMServiceType = Field(
        default=LLMServiceType.OPENAI,
        description="Active LLM service provider",
        env="LLM_SERVICE"
    )

    # ----- OpenAI 配置 -----
    OPENAI_BASE_URL: str = Field(
        default="https://api.openai.com/v1",
        description="OpenAI API endpoint",
        env="OPENAI_BASE_URL"
    )
    
    OPENAI_API_KEY: Optional[str] = Field(
        default=None,
        description="OpenAI API key",
        env="OPENAI_API_KEY"
    )
    
    OPENAI_MODEL: str = Field(
        default="gpt-4.1",  # 必须提供值
        description="模型名称 (如 gpt-4.1 或 gemini-2.5-pro-exp-03-25)",
        env="OPENAI_MODEL"
    )
    # ----- 新增 图片格式配置参数 -----
    OUTPUT_IMAGE_FORMAT: str = Field(
        default="png",  # 默认使用PNG格式
        description="Output image format (png/jpg/webp)",
        env="OUTPUT_IMAGE_FORMAT"
    )
    # ----- 新增 GOOGLE_API_KEY 配置 -----
    # GOOGLE_API_KEY: Optional[str] = Field(
    #     default=None,
    #     description="Google API key",
    #     env="GOOGLE_API_KEY"
    # )
    
        # ----- 新增 FONT_PATH 配置 -----
    FONT_PATH: str = Field(
        default= "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",  # macOS上的Arial Unicode字体路径
        description="Font file path for text processing",
        env="FONT_PATH"
    )
    
    FONT_NAME: str = Field(
        default="Arial",
        description="Font name for text rendering",
        env="FONT_NAME"
    )    

    # ----- 系统配置 -----
    OUTPUT_DIR: str = Field(
        default=os.path.join(BASE_DIR, "output"),
        description="Output directory",
        env="OUTPUT_DIR"
    )
    
    OUTPUT_FORMAT: str = Field(
        default="markdown",
        description="Output file format",
        env="OUTPUT_FORMAT"
    )
    
    DEBUG: bool = Field(
        default=False,
        description="Enable debug mode",
        env="DEBUG"
    )

    DEBUG_LEVEL: str = Field(
        default="info",
        description="调试模式: info|verbose|debug",
        env=" DEBUG_LEVEL"
    )
    # 在Settings类中添加以下字段
    FORCE_OCR: bool = Field(
        default=False,
        description="强制使用OCR处理所有文本",
        env="FORCE_OCR"
    )

    PAGE_RANGE: str = Field(
        default="all",
        description="处理的页面范围(如'1-3')",
        env="PAGE_RANGE"
    )

    LANGUAGES: str = Field(
        default="en",
        description="文档语言代码(如'zh')",
        env="LANGUAGES"
    )

    MAX_RETRIES: int = Field(
        default=3,
        description="最大重试次数",
        env="MAX_RETRIES"
    )


    # ==================== 添加计算属性（@computed_field） ====================
    @computed_field
    @property
    def TORCH_DEVICE(self) -> str:
        if torch.cuda.is_available():
            return "cuda"
        if torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    @computed_field
    @property
    def MODEL_DTYPE(self) -> torch.dtype:
        return torch.bfloat16 if self.TORCH_DEVICE == "cuda" else torch.float32


    @computed_field
    @property
    def TORCH_DEVICE(self) -> str:
        if torch.cuda.is_available():
            return "cuda"
        if torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    @computed_field
    @property
    def TORCH_DEVICE_MODEL(self) -> str:
        """兼容旧代码的别名"""
        return self.TORCH_DEVICE

    @computed_field
    @property
    def MODEL_DTYPE(self) -> torch.dtype:
        return torch.bfloat16 if self.TORCH_DEVICE == "cuda" else torch.float32
    # ==================== 配置源设置 ====================
    class Config:
        extra = "ignore"


# marker/settings.py 最后添加
settings = Settings()    

# ==================== 测试函数 ====================
def validate_settings():
    """验证配置加载是否正确"""
    # 先加载环境变量
    load_environment_variables()
    
    # 实例化 Settings 类
    settings = Settings()
    
    print("\n" + "="*50)
    print("🔍 配置验证结果")
    print(f"LLM 服务: {settings.LLM_SERVICE}")
    print(f"OpenAI 模型: {settings.OPENAI_MODEL}")
    print(f"API 端点: {settings.OPENAI_BASE_URL}")
    print(f"API 密钥: {'***'+settings.OPENAI_API_KEY[-3:] if settings.OPENAI_API_KEY else '未设置'}")
    print(f"输出目录: {settings.OUTPUT_DIR}")
    print(f"计算设备: {settings.TORCH_DEVICE}")
    print("="*50 + "\n")

if __name__ == "__main__":
    validate_settings()
    
