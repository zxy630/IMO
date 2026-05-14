from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_community.chat_models.tongyi import ChatTongyi
import requests

from app.config import settings
from app.services.rag_service import get_user_city, get_weather


QWEN_MODEL_PREFIXES = ("qwen-",)
DEEPSEEK_MODEL_PREFIXES = ("deepseek-",)
GPT_MODEL_PREFIXES = ("gpt-", "o1", "o3", "o4")


def get_model_provider(model: str) -> str:
    model_name = (model or "").strip().lower()
    if model_name.startswith(QWEN_MODEL_PREFIXES):
        return "qwen"
    if model_name.startswith(DEEPSEEK_MODEL_PREFIXES):
        return "deepseek"
    if model_name.startswith(GPT_MODEL_PREFIXES):
        return "gpt"
    return "unknown"


def chat_with_model(model: str, message: str) -> str:
    provider = get_model_provider(model)
    if provider == "qwen":
        return chat_with_tongyi(model, message)
    if provider == "deepseek":
        return chat_with_openai_compatible(
            model=model,
            message=message,
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            provider_name="DeepSeek",
        )
    if provider == "gpt":
        return chat_with_openai_compatible(
            model=model,
            message=message,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            provider_name="OpenAI",
        )
    raise ValueError(f"不支持的模型: {model}")


def chat_with_openai_compatible(
    model: str,
    message: str,
    api_key: str | None,
    base_url: str,
    provider_name: str,
) -> str:
    if not api_key:
        raise ValueError(f"未配置 {provider_name} API Key")

    url = f"{base_url.rstrip('/')}/chat/completions"
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个中文 AI 助手，请用简洁、准确、友好的中文回答用户。",
                },
                {"role": "user", "content": message},
            ],
            "temperature": 0.7,
        },
        timeout=60,
    )
    response.raise_for_status()
    result = response.json()
    choices = result.get("choices") or []
    if not choices:
        raise ValueError(f"{provider_name} 未返回有效回复")
    content = ((choices[0].get("message") or {}).get("content") or "").strip()
    if not content:
        raise ValueError(f"{provider_name} 返回内容为空")
    return content


def chat_with_tongyi(model: str, message: str) -> str:
    if not settings.DASHSCOPE_API_KEY:
        raise ValueError("未配置 DASHSCOPE_API_KEY")
    llm = ChatTongyi(model=model, dashscope_api_key=settings.DASHSCOPE_API_KEY)

    tools = [get_user_city, get_weather]
    llm_with_tools = llm.bind_tools(tools)
    tool_map = {t.name: t for t in tools}

    messages = [
        SystemMessage(
            content=(
                "你是一个中文AI助手。你可以按需调用工具获取信息。"
                "如果用户问天气但没说城市，请先调用 get_user_city 再调用 get_weather。"
            )
        ),
        HumanMessage(content=message),
    ]

    # 简单的工具调用循环，避免死循环
    for _ in range(4):
        ai_msg = llm_with_tools.invoke(messages)
        messages.append(ai_msg)

        tool_calls = getattr(ai_msg, "tool_calls", None) or []
        if not tool_calls:
            content = ai_msg.content
            if isinstance(content, list):
                return "".join(str(x) for x in content)
            return str(content)

        for call in tool_calls:
            name = call.get("name")
            args = call.get("args") or {}
            tool = tool_map.get(name)
            if not tool:
                result = f"工具{name}不存在"
            else:
                try:
                    result = tool.invoke(args)
                except Exception as exc:
                    result = f"工具{name}调用失败: {exc}"
            messages.append(ToolMessage(content=str(result), tool_call_id=call.get("id", "")))

    return "工具调用次数过多，已终止。请换一种问法或稍后再试。"
    if isinstance(content, list):
        return "".join(str(x) for x in content)
    return str(content)
