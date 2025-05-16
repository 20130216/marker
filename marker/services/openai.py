import base64
import json
import time
from io import BytesIO
from typing import Annotated, List, Union

import openai
import PIL
from openai import APITimeoutError, RateLimitError
from PIL import Image
from pydantic import BaseModel

from marker.schema.blocks import Block
from marker.services import BaseService

class OpenAIService(BaseService):
    openai_base_url: Annotated[
        str,
        "The base url to use for OpenAI-like models.  No trailing slash."
    ] = "https://api.openai.com/v1"
    openai_model: Annotated[
        str,
        "The model name to use for OpenAI-like model."
    ] = "gpt-4o-mini"
    openai_api_key: Annotated[
        str,
        "The API key to use for the OpenAI-like service."
    ] = None

    def image_to_base64(self, image: PIL.Image.Image):
        image_bytes = BytesIO()
        image.save(image_bytes, format="WEBP")
        return base64.b64encode(image_bytes.getvalue()).decode("utf-8")

    def prepare_images(
        self, images: Union[Image.Image, List[Image.Image]]
    ) -> List[dict]:
        if isinstance(images, Image.Image):
            images = [images]

        return [
            {
                "type": "image_url",
                "image_url": {
                    "url": "data:image/webp;base64,{}".format(
                        self.image_to_base64(img)
                    ),
                }
            }
            for img in images
        ]

    def __call__(
        self,
        prompt: str,
        image: PIL.Image.Image | List[PIL.Image.Image],
        block: Block,
        response_schema: type[BaseModel],
        max_retries: int | None = None,
        timeout: int | None = None,
    ):
        # 添加调试信息，输出请求的模型名称和输入的消息内容
        print("\n\n===以下是 marker/services/openai.py 中的反馈 ===")        
        print(f"🔥 openai.py的__call__中调用的模型名称（执行API调用时，确实会被调用的模型）: {self.openai_model}")  # 显示当前模型
        # print(
        #     f"🔥 openai.py 提醒，请求参数-- prompt来自于硬编码，image是图片数据的base64编码格式（当解析PDF文档并将其传递给模型时，PDF中的图片会被转换为 base64 编码，并作为 image 参数传入 API 请求中。）：prompt={prompt}, image={image}")

        # 确保传递的 messages 内容正确
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    *self.prepare_images(image),
                ],
            }
        ]
        
        # 添加调试代码，输出请求的消息内容
        print(f"🔥 marker/services/openai.py 中传递的消息: {messages}")  # 输出传递给模型的消息体 
        
        if max_retries is None:
            max_retries = self.max_retries

        if timeout is None:
            timeout = self.timeout

        client = self.get_client()
        tries = 0
        print("🔥 即将调用API，准备发送请求...")
        
        while tries < max_retries:
            try:
                # 1. 执行API请求
                response = client.beta.chat.completions.parse(
                    extra_headers={
                        "X-Title": "Marker",
                        "HTTP-Referer": "https://github.com/VikParuchuri/marker"
                    },
                    model=self.openai_model,
                    messages=messages,
                    timeout=timeout,
                    response_format=response_schema,
                )

                # 2. 增强调试信息
                debug_info = {
                    "status": getattr(response, "status_code", "N/A"),
                    "model": self.openai_model,
                    "tries_left": max_retries - tries - 1
                }
                print(f"🔥 响应状态: {debug_info}")

                # 3. 获取响应内容（安全方式）
                response_text = getattr(response.choices[0].message, 'content', '')
                if not response_text:
                    raise ValueError("空响应内容")

                # 4. JSON解析增强
                try:
                    parsed = json.loads(response_text)
                    print("✅ 成功解析JSON响应")
                    return parsed
                except json.JSONDecodeError:
                    # 尝试修复常见JSON格式问题
                    cleaned = response_text.strip()
                    if cleaned.startswith(('{', '[')) and cleaned.endswith(('}', ']')):
                        try:
                            return json.loads(cleaned)
                        except json.JSONDecodeError as e:
                            print(f"🛑 修复JSON失败: {e}\n原始内容:\n{response_text[:300]}...")
                    raise

            except (APITimeoutError, RateLimitError) as e:
                # 专用错误处理
                tries += 1
                wait_time = min(tries * 3, 10)  # 上限10秒
                print(f"⏳ 速率限制/超时({tries}/{max_retries}): {e}. 等待 {wait_time}s...")
                time.sleep(wait_time)
                continue

            except json.JSONDecodeError as e:
                print(f"🛑 JSON解析失败: {e}")
                if tries == max_retries - 1:  # 最后一次尝试
                    print(f"🔥 原始响应内容:\n{response_text[:500]}...")  # 显示前500字符
                tries += 1
                time.sleep(1)
                continue

            except Exception as e:
                print(f"🛑 意外错误: {type(e).__name__}: {str(e)}")
                tries += 1
                if tries < max_retries:
                    time.sleep(1)
                continue
            
        print("===以上是 marker/services/openai.py 中的反馈 ===\n")  # 新增行
        print("❌ 达到最大重试次数，返回空结果")
        return {}  # 确保始终有返回值


    def get_client(self) -> openai.OpenAI:
        return openai.OpenAI(api_key=self.openai_api_key, base_url=self.openai_base_url)
