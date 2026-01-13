# 快速开始

## 5分钟快速入门

### 安装依赖

```bash
pip install transformers torch
```

### 最小示例

```python
from llmrankers.universal_setwise import UniversalSetwiseLlmRanker
from llmrankers.universal_ranker import SearchResult

# 1️⃣ 初始化ranker（任何HuggingFace模型！）
ranker = UniversalSetwiseLlmRanker("google/flan-t5-base", device='cuda')

# 2️⃣ 准备待排序文档
docs = [
    SearchResult("1", 10, "Machine learning is a subset of AI"),
    SearchResult("2", 9, "Deep learning uses neural networks"),
    SearchResult("3", 8, "NLP processes natural language"),
    SearchResult("4", 7, "Computer vision processes images"),
    SearchResult("5", 6, "Reinforcement learning uses rewards"),
]

# 3️⃣ 执行重排序
query = "machine learning techniques"
results = ranker.rerank(query, docs)

# 4️⃣ 查看结果
for i, doc in enumerate(results[:3]):
    print(f"{i+1}. Doc {doc.docid} (score: {doc.score})")
```

**输出:**
```
1. Doc 1 (score: -1)
2. Doc 2 (score: -2)
3. Doc 3 (score: -3)
```

---

## 与不同模型集成

### 使用T5

```python
ranker = UniversalSetwiseLlmRanker("google/flan-t5-large", k=10)
results = ranker.rerank(query, docs)
```

### 使用LLaMA

```python
ranker = UniversalSetwiseLlmRanker("meta-llama/Llama-2-7b-chat-hf")
results = ranker.rerank(query, docs)
```

### 使用Mistral

```python
ranker = UniversalSetwiseLlmRanker("mistralai/Mistral-7B-Instruct-v0.1")
results = ranker.rerank(query, docs)
```

### 使用任何其他模型

```python
ranker = UniversalSetwiseLlmRanker("your-hf-model-name")
results = ranker.rerank(query, docs)
```

---

## 常见配置

### 快速模式（低延迟）
```python
ranker = UniversalSetwiseLlmRanker(
    model_name_or_path="google/flan-t5-base",
    k=5,
    num_child=2,  # 减少比较
    device='cuda'
)
```

### 平衡模式（推荐）
```python
ranker = UniversalSetwiseLlmRanker(
    model_name_or_path="google/flan-t5-large",
    k=10,
    num_child=3,  # 标准值
    method="heapsort",
    device='cuda'
)
```

### 高精度模式（需要投票）
```python
from llmrankers.universal_setwise import UniversalSetwiseLlmRankerWithVoting

ranker = UniversalSetwiseLlmRankerWithVoting(
    model_name_or_path="meta-llama/Llama-2-13b-chat-hf",
    k=10,
    num_child=4,
    num_permutation=3,  # 从3个排列投票
    device='cuda'
)
```

---

## 批量处理

```python
queries = [
    "machine learning",
    "deep learning",
    "natural language processing"
]

for query in queries:
    results = ranker.rerank(query, docs)
    print(f"\n{query}:")
    for doc in results[:3]:
        print(f"  - Doc {doc.docid}")
```

---

## 自定义提示词

```python
class CustomRanker(UniversalSetwiseLlmRanker):
    def compare(self, query, docs):
        passages = "\n".join([f"[{self.CHARACTERS[i]}] {doc.text}" 
                             for i, doc in enumerate(docs)])
        
        prompt = f"""
Query: {query}

Passages:
{passages}

Which passage is most relevant? (Answer: A, B, C, ...)
"""
        output = self.adapter.generate([prompt], max_new_tokens=2)[0]
        return output[0].upper()

ranker = CustomRanker("google/flan-t5-base")
results = ranker.rerank(query, docs)
```

---

## 故障排除

### GPU内存不足？

```bash
# 使用CPU
ranker = UniversalSetwiseLlmRanker("model", device='cpu')

# 或使用更小的模型
ranker = UniversalSetwiseLlmRanker("google/flan-t5-base")  # 小模型

# 或量化
ranker = UniversalSetwiseLlmRanker("model")  # 会自动使用8-bit
```

### 模型下载缓慢？

```python
# 使用本地模型路径
ranker = UniversalSetwiseLlmRanker("/path/to/local/model")
```

### HuggingFace Hub权限错误？

```bash
# 登录HuggingFace
huggingface-cli login

# 或设置token
huggingface-cli login --token <your-token>
```

---

## 性能提示

| 操作 | 优化方案 |
|------|--------|
| 降低延迟 | 使用smaller model（flan-t5-base） + k=5 + num_child=2 |
| 提高精度 | 使用larger model + num_permutation=3 |
| 节省内存 | 使用T5-base而不是LLaMA-7b |
| 快速实验 | CPU推理用来测试，确认后用GPU |

---

## 与现有代码集成

### 方式1：直接替换（推荐）

```python
# 旧代码
# from llmrankers.setwise import SetwiseLlmRanker

# 新代码
from llmrankers.universal_setwise import UniversalSetwiseLlmRanker as SetwiseLlmRanker

# 其他代码完全不变！
ranker = SetwiseLlmRanker(model_path)
results = ranker.rerank(query, ranking)
```

### 方式2：并行使用

```python
from llmrankers.setwise import SetwiseLlmRanker  # 旧的
from llmrankers.universal_setwise import UniversalSetwiseLlmRanker  # 新的

# 旧项目用旧ranker
old_ranker = SetwiseLlmRanker("flan-t5-large")

# 新项目用新ranker
new_ranker = UniversalSetwiseLlmRanker("mistral-7b")
```

### 方式3：渐进迁移

```python
import sys

# 定义哪些模块使用新ranker
USE_UNIVERSAL = {'new_module', 'experimental'}

if sys.modules.get('__main__').__name__ in USE_UNIVERSAL:
    from llmrankers.universal_setwise import UniversalSetwiseLlmRanker as SetwiseLlmRanker
else:
    from llmrankers.setwise import SetwiseLlmRanker
```

---

## 文档导航

| 文档 | 内容 |
|------|------|
| `SOLUTION_SUMMARY.md` | 整体解决方案总结 |
| `ARCHITECTURE.md` | 详细架构设计 |
| `ARCHITECTURE_DIAGRAM.md` | 可视化架构 |
| `MIGRATION_GUIDE.md` | 迁移指南 |
| `MODEL_REFERENCE.md` | 模型参考表 |
| `example_universal_ranker.py` | 7个完整示例 |

---

## 下一步

1. ✅ 阅读本文档（已完成）
2. ⏳ 尝试最小示例
3. ⏳ 用你自己的数据测试
4. ⏳ 选择最适合的模型
5. ⏳ 集成到你的项目

---

## 获取帮助

**常见问题：**
- 支持哪些模型？→ 查看 `MODEL_REFERENCE.md`
- 如何自定义？ → 查看 `example_universal_ranker.py`
- 如何迁移现有代码？ → 查看 `MIGRATION_GUIDE.md`
- 架构是什么？ → 查看 `ARCHITECTURE_DIAGRAM.md`

---

**开始使用吧！🚀**

```python
from llmrankers.universal_setwise import UniversalSetwiseLlmRanker

# 选择你喜欢的模型
ranker = UniversalSetwiseLlmRanker("your-model-here")

# 完成！
results = ranker.rerank(query, docs)
```
