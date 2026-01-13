# 快速迁移指南

## 从现有代码迁移到通用Ranker

### 第1步：了解差异

**原始代码 (setwise.py):**
```python
from llmrankers.setwise import SetwiseLlmRanker

# 只支持T5和LLaMA
ranker = SetwiseLlmRanker(
    model_name_or_path="google/flan-t5-large",
    tokenizer_name_or_path="google/flan-t5-large",
    device='cuda',
    num_child=3,
    k=10,
    scoring='generation'  # 额外参数
)
```

**新通用代码:**
```python
from llmrankers.universal_setwise import UniversalSetwiseLlmRanker

# 支持任何HuggingFace模型！
ranker = UniversalSetwiseLlmRanker(
    model_name_or_path="google/flan-t5-large",
    device='cuda',
    num_child=3,
    k=10
)
```

### 第2步：代码迁移示例

#### 场景A：从T5/LLaMA切换到其他模型

```python
# ❌ 原始方式（不支持新模型）
ranker = SetwiseLlmRanker(
    model_name_or_path="mistralai/Mistral-7B-Instruct-v0.1",  # 会报错！
    device='cuda'
)

# ✅ 新方式（自动支持）
ranker = UniversalSetwiseLlmRanker(
    model_name_or_path="mistralai/Mistral-7B-Instruct-v0.1",
    device='cuda'
)
```

#### 场景B：现有项目的最小改动

```python
# 保留现有代码，新增通用ranker
# setwise.py (保留，不改)
# universal_setwise.py (新增)

# 逐步替换使用的Ranker类
# from llmrankers.setwise import SetwiseLlmRanker  # 旧
from llmrankers.universal_setwise import UniversalSetwiseLlmRanker as SetwiseLlmRanker  # 新

# 其他代码保持不变
ranker = SetwiseLlmRanker(...)
results = ranker.rerank(query, ranking)
```

#### 场景C：同时使用新旧代码

```python
from llmrankers.setwise import SetwiseLlmRanker as LegacySetwiseLlmRanker
from llmrankers.universal_setwise import UniversalSetwiseLlmRanker

# 旧项目使用原始
old_ranker = LegacySetwiseLlmRanker(...)

# 新项目使用通用
new_ranker = UniversalSetwiseLlmRanker(...)
```

### 第3步：逐个文件迁移

#### 迁移setwise

```bash
# 备份原文件
cp llmrankers/setwise.py llmrankers/setwise.py.bak

# 导入通用版本到现有code
# 在code_example.py中改为：
from llmrankers.universal_setwise import UniversalSetwiseLlmRanker
```

#### 迁移pairwise（如需要）

创建 `universal_pairwise.py`:

```python
from llmrankers.universal_ranker import UniversalLlmRanker, SearchResult
from llmrankers.model_adapter import LlmInferenceAdapter
from typing import List

class UniversalPairwiseLlmRanker(UniversalLlmRanker):
    def __init__(self, model_name_or_path, **kwargs):
        super().__init__(model_name_or_path, **kwargs)
        # 初始化pairwise特定的逻辑
    
    def compare(self, query: str, doc1: SearchResult, doc2: SearchResult) -> str:
        prompt = f"""Given query "{query}":
Passage A: {doc1.text}
Passage B: {doc2.text}
Which is more relevant? Answer only A or B:"""
        
        output = self.adapter.generate([prompt], max_new_tokens=1)[0]
        return "A" if "A" in output.upper() else "B"
    
    def rerank(self, query: str, ranking: List[SearchResult]) -> List[SearchResult]:
        # 实现pairwise排序逻辑
        pass
```

#### 迁移listwise（如需要）

类似地创建 `universal_listwise.py`

### 第4步：测试和验证

```python
# test_universal_ranker.py
from llmrankers.universal_setwise import UniversalSetwiseLlmRanker
from llmrankers.universal_ranker import SearchResult

def test_t5():
    ranker = UniversalSetwiseLlmRanker("google/flan-t5-base")
    docs = [
        SearchResult("1", 10, "Machine learning text"),
        SearchResult("2", 9, "Deep learning text"),
    ]
    results = ranker.rerank("query", docs)
    assert len(results) == 2
    print("✓ T5 test passed")

def test_llama():
    ranker = UniversalSetwiseLlmRanker("meta-llama/Llama-2-7b-hf")
    docs = [
        SearchResult("1", 10, "Machine learning text"),
        SearchResult("2", 9, "Deep learning text"),
    ]
    results = ranker.rerank("query", docs)
    assert len(results) == 2
    print("✓ LLaMA test passed")

def test_mistral():
    ranker = UniversalSetwiseLlmRanker("mistralai/Mistral-7B-Instruct-v0.1")
    docs = [
        SearchResult("1", 10, "Machine learning text"),
        SearchResult("2", 9, "Deep learning text"),
    ]
    results = ranker.rerank("query", docs)
    assert len(results) == 2
    print("✓ Mistral test passed")

if __name__ == "__main__":
    test_t5()
    test_llama()
    test_mistral()
    print("\n✓ All tests passed!")
```

### 第5步：性能对比

```python
import time
from llmrankers.setwise import SetwiseLlmRanker
from llmrankers.universal_setwise import UniversalSetwiseLlmRanker
from llmrankers.universal_ranker import SearchResult

# 创建测试数据
docs = [SearchResult(str(i), 10-i, f"Text {i}") for i in range(10)]

# 测试原始版本
start = time.time()
ranker1 = SetwiseLlmRanker("google/flan-t5-base", device='cuda')
results1 = ranker1.rerank("query", docs)
time1 = time.time() - start

# 测试通用版本
start = time.time()
ranker2 = UniversalSetwiseLlmRanker("google/flan-t5-base", device='cuda')
results2 = ranker2.rerank("query", docs)
time2 = time.time() - start

print(f"原始版本: {time1:.2f}s")
print(f"通用版本: {time2:.2f}s")
print(f"差异: {abs(time1-time2):.2f}s (通常无显著差异)")
```

## 常见迁移问题

### Q1: 是否需要重新训练模型？
**A:** 不需要，推理代码改变不影响模型权重。

### Q2: 现有脚本会中断吗？
**A:** 如果保留原始文件，不会。可以并行使用两个版本。

### Q3: 新模型需要特殊处理吗？
**A:** 大多数HuggingFace模型开箱即用，特殊情况可以继承类并重写方法。

### Q4: 内存占用会增加吗？
**A:** 不会，适配器层很轻量级。

### Q5: API接口是否兼容？
**A:** 是的！`rerank()` 方法签名相同。

## 检查清单

- [ ] 新建 `model_adapter.py` 文件
- [ ] 新建 `universal_ranker.py` 文件
- [ ] 新建 `universal_setwise.py` 文件
- [ ] 在项目中测试新ranker
- [ ] 对比新旧版本的结果
- [ ] 更新import语句
- [ ] 运行现有测试
- [ ] 备份原始文件
- [ ] 文档更新

## 回滚方案

如果遇到问题，可以快速回滚：

```python
# 恢复到原始版本
import shutil
shutil.copy('llmrankers/setwise.py.bak', 'llmrankers/setwise.py')

# 或改回import
from llmrankers.setwise import SetwiseLlmRanker  # 原始版本
# from llmrankers.universal_setwise import UniversalSetwiseLlmRanker  # 新版本
```

## 下一步

1. ✅ 创建通用adapter和ranker
2. ✅ 在新项目中使用
3. ⏳ 逐步迁移现有代码
4. ⏳ 删除原始文件（可选）
5. ⏳ 为pairwise和listwise创建通用版本
