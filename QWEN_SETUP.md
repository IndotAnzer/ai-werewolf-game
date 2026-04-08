# 通义千问配置指南

## 🎯 快速配置步骤

### 1. 获取阿里云 API Key

1. 访问 [阿里云 DashScope 控制台](https://dashscope.console.aliyun.com/)
2. 注册/登录阿里云账号
3. 开通 DashScope 服务（免费额度）
4. 在"API-KEY管理"中创建新的 API Key
5. 复制 API Key（格式：`sk-xxxxxxxx`）

### 2. 配置环境变量

项目已经为你准备好了配置文件模板，只需编辑即可：

```bash
# 复制配置文件
cp .env.qwen .env
```

编辑 `.env` 文件，填入你的 API Key：

```env
DASHSCOPE_API_KEY=你的通义千问API-KEY
MODEL_NAME=qwen-plus  # 可选：qwen-turbo, qwen-plus, qwen-max
```

### 3. 开始游戏

```bash
python main.py
```

## 📋 配置文件说明 (.env.qwen)

```env
# 阿里云 DashScope API Key（必填）
DASHSCOPE_API_KEY=your-api-key-here

# 模型选择（可选，默认 qwen-plus）
# - qwen-turbo: 快速便宜，适合测试
# - qwen-plus: 性能强劲，推荐日常使用
# - qwen-max: 最强性能，适合复杂推理
MODEL_NAME=qwen-plus

# API 端点（通常不需要修改）
DASHSCOPE_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
```

## 🔧 代码中使用

项目已内置通义千问支持，可以直接运行 `python main.py`，程序会询问你选择使用通义千问还是 OpenAI。

### 在代码中直接使用

```python
from utils.model_config import get_qwen_llm

# 获取通义千问实例
llm = get_qwen_llm(model_name="qwen-plus", temperature=0.8)

# 使用
response = llm.invoke("你好")
print(response.content)
```

## 💰 费用说明

- **qwen-turbo**: 非常便宜，适合测试
- **qwen-plus**:性价比高，推荐使用
- **qwen-max**: 较贵，但推理能力最强

阿里云有免费额度，新用户可以免费使用一段时间。

## ❓ 常见问题

### Q: 提示 "API Key 无效"
A: 请检查 `.env` 文件中的 `DASHSCOPE_API_KEY` 是否正确填写，不要有多余的空格。

### Q: 提示 "模型不存在"
A: 确保你选择的模型名称正确，可选：`qwen-turbo`, `qwen-plus`, `qwen-max`

### Q: 连接超时
A: 检查网络连接，或尝试使用代理。

### Q: 如何切换回 OpenAI？
A: 在 `main.py` 运行时会询问你选择模型提供商，选择 OpenAI 并配置 `.env` 中的 `OPENAI_API_KEY` 即可。

## 🧪 测试连接

```bash
# 测试通义千问连接
python utils/model_config.py
```

如果显示"✅ 连接成功"，说明配置正确！

## 📝 多模型切换

项目支持同时配置多个模型 Provider：

- 通义千问：编辑 `.env` 中的 `DASHSCOPE_API_KEY`
- OpenAI：编辑 `.env` 中的 `OPENAI_API_KEY`

运行 `main.py` 时选择即可。
