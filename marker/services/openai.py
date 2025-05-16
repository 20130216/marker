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
        print(f"🔥 调用的模型名称: {self.openai_model}")  # 显示当前模型
        print(
            f"🔥 openai.py 提醒，请求参数-- prompt来自于硬编码，image是图片数据的base64编码格式（当解析PDF文档并将其传递给模型时，PDF中的图片会被转换为 base64 编码，并作为 image 参数传入 API 请求中。）：prompt={prompt}, image={image}")

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
        print(f"🔥 传递的消息体: {messages}")  # 输出传递给模型的消息体

        if max_retries is None:
            max_retries = self.max_retries

        if timeout is None:
            timeout = self.timeout

        client = self.get_client()
        tries = 0
        while tries < max_retries:
            try:
                # 调用模型并捕获响应
                response = client.beta.chat.completions.parse(
                    extra_headers={
                        "X-Title": "Marker",
                        "HTTP-Referer": "https://github.com/VikParuchuri/marker",
                    },
                    model=self.openai_model,
                    messages=messages,
                    timeout=timeout,
                    response_format=response_schema,
                )
                print(f"🔥 模型响应: {response}")  # 输出模型的响应
                response_text = response.choices[0].message.content
                total_tokens = response.usage.total_tokens
                block.update_metadata(llm_tokens_used=total_tokens, llm_request_count=1)
                return json.loads(response_text)

            except (APITimeoutError, RateLimitError) as e:
                # 处理超时或速率限制错误
                tries += 1
                wait_time = tries * 3
                print(
                    f"Rate limit error: {e}. Retrying in {wait_time} seconds... (Attempt {tries}/{max_retries})"
                )
                time.sleep(wait_time)
            except Exception as e:
                print(f"🔥 出现错误: {e}")
                break

        return {}

    def get_client(self) -> openai.OpenAI:
        return openai.OpenAI(api_key=self.openai_api_key, base_url=self.openai_base_url)
