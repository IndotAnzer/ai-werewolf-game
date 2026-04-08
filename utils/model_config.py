import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def get_qwen_llm(model_name: str = None, temperature: float = 0.8) -> ChatOpenAI:
    """
    获取通义千问 LLM 实例
    
    参数:
        model_name: 模型名称，可选 'qwen-turbo', 'qwen-plus', 'qwen-max'
        temperature: 温度参数，控制随机性 (0.0-2.0)
    """
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("请设置 DASHSCOPE_API_KEY 环境变量！")
    
    model = model_name or os.getenv("MODEL_NAME", "qwen-plus")
    base_url = os.getenv("DASHSCOPE_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key,
        base_url=base_url
    )


def get_openai_llm(model_name: str = None, temperature: float = 0.8) -> ChatOpenAI:
    """
    获取 OpenAI LLM 实例
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("请设置 OPENAI_API_KEY 环境变量！")
    
    model = model_name or os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key
    )


def get_llm(provider: str = "qwen", **kwargs) -> ChatOpenAI:
    """
    统一获取 LLM 实例
    
    参数:
        provider: 模型提供商，可选 'qwen' 或 'openai'
        **kwargs: 传递给 LLM 的其他参数
    """
    if provider.lower() == "qwen":
        return get_qwen_llm(**kwargs)
    elif provider.lower() == "openai":
        return get_openai_llm(**kwargs)
    else:
        raise ValueError(f"不支持的模型提供商: {provider}，请使用 'qwen' 或 'openai'")


if __name__ == "__main__":
    print("测试通义千问连接...")
    try:
        llm = get_qwen_llm()
        response = llm.invoke("你好，请回复'连接成功'")
        print(f"✅ {response.content}")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("\n请确保已经：")
        print("1. 复制配置文件: cp .env.qwen .env")
        print("2. 在 .env 中填入你的 DASHSCOPE_API_KEY")
