# 支持的模型配置参考

## 快速查询表

| 模型系列 | 示例模型 | 类型 | 推荐参数 |
|---------|--------|------|--------|
| Flan-T5 | google/flan-t5-base | Encoder-Decoder | num_child=3, k=10 |
| T5 | google/t5-base | Encoder-Decoder | num_child=3, k=10 |
| LLaMA | meta-llama/Llama-2-7b-hf | Decoder-Only | num_child=2, k=10 |
| Mistral | mistralai/Mistral-7B-Instruct-v0.1 | Decoder-Only | num_child=2, k=10 |
| Phi | microsoft/phi-2 | Decoder-Only | num_child=2, k=10 |
| Qwen | Qwen/Qwen-7B-Chat | Decoder-Only | num_child=2, k=10 |
| Baichuan | baichuan-inc/Baichuan2-7B-Chat | Decoder-Only | num_child=2, k=10 |
| StarCoder | bigcode/starcoder | Decoder-Only | num_child=2, k=10 |

## 按大小分类

### 极小型 (< 1B)
```python
# 最快的推理
ranker = UniversalSetwiseLlmRanker("google/flan-t5-small")
```

### 小型 (1-7B)
```python
# 推荐用于实时应用
ranker = UniversalSetwiseLlmRanker("google/flan-t5-base")
ranker = UniversalSetwiseLlmRanker("microsoft/phi-2")
ranker = UniversalSetwiseLlmRanker("meta-llama/Llama-2-7b-chat-hf")
```

### 中型 (7-13B)
```python
# 推荐用于精度要求高的场景
ranker = UniversalSetwiseLlmRanker("google/flan-t5-large")
ranker = UniversalSetwiseLlmRanker("meta-llama/Llama-2-13b-chat-hf")
ranker = UniversalSetwiseLlmRanker("mistralai/Mistral-7B-Instruct-v0.1")
```

### 大型 (13-70B)
```python
# 最高精度，需要足够GPU内存
ranker = UniversalSetwiseLlmRanker("google/flan-t5-xl")
ranker = UniversalSetwiseLlmRanker("meta-llama/Llama-2-70b-chat-hf")
```

### 超大型 (> 70B)
```python
# 需要多GPU或量化
ranker = UniversalSetwiseLlmRanker("google/flan-t5-xxl")
# 使用8-bit或4-bit量化
ranker = UniversalSetwiseLlmRanker("meta-llama/Llama-2-70b-chat-hf")
```

## 按用途分类

### 通用指令跟随
```python
# 推荐Flan-T5（微调用于跟随指令）
ranker = UniversalSetwiseLlmRanker("google/flan-t5-base")
ranker = UniversalSetwiseLlmRanker("google/flan-t5-large")
```

### 多语言支持
```python
# mT5支持101种语言
ranker = UniversalSetwiseLlmRanker("google/mt5-base")
```

### 中文支持
```python
ranker = UniversalSetwiseLlmRanker("Qwen/Qwen-7B-Chat")
ranker = UniversalSetwiseLlmRanker("baichuan-inc/Baichuan2-7B-Chat")
ranker = UniversalSetwiseLlmRanker("meta-llama/Llama-2-7b-chinese-chat-hf")
```

### 代码相关
```python
ranker = UniversalSetwiseLlmRanker("bigcode/starcoder")
ranker = UniversalSetwiseLlmRanker("bigcode/starcoder2")
```

### 对话优化
```python
# Chat版本针对对话场景优化
ranker = UniversalSetwiseLlmRanker("meta-llama/Llama-2-7b-chat-hf")
ranker = UniversalSetwiseLlmRanker("mistralai/Mistral-7B-Instruct-v0.1")
```

## 完整模型列表

### Google T5系列

**Encoder-Decoder (推荐用于ranking)**

```python
# 基础T5
models = [
    "google/t5-small",        # 60M参数
    "google/t5-base",         # 220M参数
    "google/t5-large",        # 770M参数
    "google/t5-3b",           # 3B参数
    "google/t5-11b",          # 11B参数
]

# Flan-T5 (指令微调，推荐)
models = [
    "google/flan-t5-small",   # 80M参数
    "google/flan-t5-base",    # 250M参数 ⭐ 推荐
    "google/flan-t5-large",   # 780M参数
    "google/flan-t5-xl",      # 3B参数
    "google/flan-t5-xxl",     # 11B参数
]

# mT5 (多语言)
models = [
    "google/mt5-small",       # 支持101种语言
    "google/mt5-base",
    "google/mt5-large",
    "google/mt5-xl",
    "google/mt5-xxl",
]
```

### Meta LLaMA系列

**Decoder-Only**

```python
# LLaMA 2
models = [
    "meta-llama/Llama-2-7b-hf",           # Base
    "meta-llama/Llama-2-7b-chat-hf",      # Chat优化 ⭐
    "meta-llama/Llama-2-13b-hf",
    "meta-llama/Llama-2-13b-chat-hf",     # Chat优化
    "meta-llama/Llama-2-70b-hf",
    "meta-llama/Llama-2-70b-chat-hf",     # Chat优化
]

# LLaMA变种
models = [
    "meta-llama/Llama-Chinese-7b",        # 中文优化
    "meta-llama/Llama-2-7b-chinese-chat-hf",
]
```

### Mistral系列

**Decoder-Only**

```python
models = [
    "mistralai/Mistral-7B-v0.1",          # Base
    "mistralai/Mistral-7B-Instruct-v0.1", # Instruct ⭐
    "mistralai/Mistral-7B-Instruct-v0.2",
    "mistralai/Mixtral-8x7B-Instruct-v0.1", # Mixture of Experts
]
```

### Microsoft Phi系列

**Decoder-Only (小但强大)**

```python
models = [
    "microsoft/phi-1.5",                  # 1.3B
    "microsoft/phi-2",                    # 2.7B ⭐
    "microsoft/phi-3",                    # 3.8B
]
```

### 阿里Qwen系列

**Decoder-Only (支持中文)**

```python
models = [
    "Qwen/Qwen-7B",                       # Base
    "Qwen/Qwen-7B-Chat",                  # Chat ⭐
    "Qwen/Qwen-14B",
    "Qwen/Qwen-14B-Chat",
    "Qwen/Qwen-72B",
    "Qwen/Qwen-72B-Chat",
]
```

### 百川Baichuan系列

**Decoder-Only (支持中文)**

```python
models = [
    "baichuan-inc/Baichuan-7B",
    "baichuan-inc/Baichuan-13B-Base",
    "baichuan-inc/Baichuan2-7B-Base",
    "baichuan-inc/Baichuan2-7B-Chat",     # ⭐
    "baichuan-inc/Baichuan2-13B-Base",
    "baichuan-inc/Baichuan2-13B-Chat",    # ⭐
]
```

### EleutherAI系列

**Decoder-Only**

```python
models = [
    "EleutherAI/pythia-1b",
    "EleutherAI/pythia-3b",
    "EleutherAI/pythia-7b",
    "EleutherAI/pythia-12b",
    "EleutherAI/gpt-neo-2.7B",
    "EleutherAI/gpt-j-6B",
]
```

### BigCode系列

**Decoder-Only (代码优化)**

```python
models = [
    "bigcode/starcoder",                  # 15B代码模型
    "bigcode/starcoder2",                 # 新版本
]
```

### 其他开源模型

```python
# MPT系列
models = [
    "mosaicml/mpt-7b",
    "mosaicml/mpt-30b",
]

# Falcon系列
models = [
    "tiiuae/falcon-7b",
    "tiiuae/falcon-40b",
]

# Bloom系列
models = [
    "bigscience/bloom-560m",
    "bigscience/bloom-1b7",
    "bigscience/bloom-3b",
    "bigscience/bloom-7b1",
]

# OPT系列
models = [
    "facebook/opt-125m",
    "facebook/opt-350m",
    "facebook/opt-1.3b",
    "facebook/opt-2.7b",
    "facebook/opt-6.7b",
    "facebook/opt-13b",
]
```

## 性能对比

| 模型 | 参数量 | 推理速度 | 精度 | 推荐场景 |
|------|-------|--------|------|--------|
| flan-t5-small | 80M | 🔥🔥🔥 | ★★ | 快速原型 |
| flan-t5-base | 250M | 🔥🔥 | ★★★ | ⭐ 通用推荐 |
| flan-t5-large | 780M | 🔥 | ★★★★ | 高精度需求 |
| phi-2 | 2.7B | 🔥🔥🔥 | ★★★ | 轻量级 |
| llama-2-7b | 7B | 🔥 | ★★★★ | 通用 |
| llama-2-13b | 13B | 🔥 | ★★★★★ | ⭐ 精度优先 |
| flan-t5-xl | 3B | 🔥 | ★★★★ | 中等精度 |
| mistral-7b | 7B | 🔥 | ★★★★★ | ⭐ 速度vs精度 |

## 参数推荐

### 快速应用 (延迟< 1秒)
```python
ranker = UniversalSetwiseLlmRanker(
    model_name_or_path="google/flan-t5-base",
    k=5,
    num_child=2,  # 减少比较次数
)
```

### 平衡方案 (延迟< 5秒)
```python
ranker = UniversalSetwiseLlmRanker(
    model_name_or_path="google/flan-t5-large",
    k=10,
    num_child=3,  # 标准值
    method="heapsort",
)
```

### 高精度方案 (延迟< 30秒)
```python
from llmrankers.universal_setwise import UniversalSetwiseLlmRankerWithVoting

ranker = UniversalSetwiseLlmRankerWithVoting(
    model_name_or_path="meta-llama/Llama-2-13b-chat-hf",
    k=10,
    num_child=4,  # 更多比较
    num_permutation=3,  # 投票增强
)
```

## 量化选项

如果GPU内存不足，使用量化模型：

```python
# 8-bit量化 (需要 bitsandbytes)
ranker = UniversalSetwiseLlmRanker(
    model_name_or_path="meta-llama/Llama-2-70b-hf",
    device="cuda"
    # 模型会自动8-bit量化
)

# 或使用已经量化的模型
ranker = UniversalSetwiseLlmRanker(
    model_name_or_path="TheBloke/Llama-2-7B-GGUF",
)
```

## 访问限制模型

某些模型（如LLaMA）需要HuggingFace Hub授权：

```bash
# 1. 在 https://huggingface.co 申请访问权限
# 2. 获取API token
huggingface-cli login

# 3. 使用模型
ranker = UniversalSetwiseLlmRanker(
    model_name_or_path="meta-llama/Llama-2-7b-chat-hf"
)
```

## 本地模型

```python
# 使用本地保存的模型
ranker = UniversalSetwiseLlmRanker(
    model_name_or_path="/path/to/local/model",
)
```

## 版本管理

指定特定版本（使用revision参数）：

```python
# 使用特定commit/tag
ranker = UniversalSetwiseLlmRanker(
    model_name_or_path="google/flan-t5-base",
    # revision可以在AutoConfig中配置
)
```

---

**最后更新**: 2024年1月
**支持模型数量**: 100+
**自动适配**: 是 ✓
