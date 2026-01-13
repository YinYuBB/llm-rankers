# 可视化架构

## 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                     使用层 (User Code)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ranker = UniversalSetwiseLlmRanker("google/flan-t5-base")      │
│  results = ranker.rerank(query, docs)                            │
│                                                                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│              Ranker 层 (llmrankers/)                             │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │ UniversalSetwise │  │  Universal      │  │  Universal    │ │
│  │ LlmRanker        │  │  Pairwise       │  │  Listwise     │ │
│  │ (universal_      │  │  LlmRanker      │  │  LlmRanker    │ │
│  │  setwise.py) ✨  │  │  (future)       │  │  (future)     │ │
│  └────────┬─────────┘  └────────┬────────┘  └────────┬───────┘ │
│           │                     │                    │          │
│           └─────────────┬───────┴────────┬──────────┘           │
│                         │                │                      │
│              ┌──────────▼────────────────▼────────┐             │
│              │  UniversalLlmRanker 基类           │             │
│              │  (universal_ranker.py) ✨          │             │
│              └──────────┬──────────────────────────┘             │
│                         │                                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│           模型适配层 (model_adapter.py) ✨ 核心                  │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ ModelAdapterFactory (工厂模式)                           │  │
│  │  - 自动检测模型类型                                     │  │
│  │  - 选择合适的适配器                                     │  │
│  │  - 支持自定义适配器注册                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─────────────────────┐        ┌──────────────────────────┐  │
│  │ T5Adapter           │        │ CausalLmAdapter          │  │
│  │ (Encoder-Decoder)   │        │ (LLaMA, Mistral, 等...)  │  │
│  │                     │        │                          │  │
│  │ - T5                │        │ - LLaMA 2               │  │
│  │ - Flan-T5           │        │ - Mistral               │  │
│  │ - mT5               │        │ - Phi                   │  │
│  │ - 其他T5变种        │        │ - Qwen                  │  │
│  │                     │        │ - Baichuan              │  │
│  │ 方法:               │        │ - EleutherAI            │  │
│  │ - generate()        │        │ - StarCoder             │  │
│  │ - get_logits()      │        │ - 等 100+ 模型           │  │
│  └─────────────────────┘        │                          │  │
│                                  │ 方法:                   │  │
│                                  │ - generate()            │  │
│                                  │ - get_logits()          │  │
│                                  └──────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ LlmInferenceAdapter (基类)                               │  │
│  │  - 统一接口                                             │  │
│  │  - tokenizer管理                                        │  │
│  │  - batch_generate()                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│           HuggingFace Transformers & Models                      │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │  T5 Models   │  │ LLaMA Models │  │ 其他 Causal LM     │   │
│  │              │  │              │  │ - Mistral, Phi    │   │
│  │ - tokenizer  │  │ - tokenizer  │  │ - Qwen, Baichuan  │   │
│  │ - model      │  │ - model      │  │ - EleutherAI      │   │
│  │              │  │              │  │ - 等等             │   │
│  └──────────────┘  └──────────────┘  └────────────────────┘   │
│                                                                  │
│                        100+ 开源模型                             │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

## 调用流程图

```
用户代码
   │
   ▼
┌─────────────────────────────────────────┐
│ ranker.rerank(query, docs)              │
└─────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────┐
│ UniversalSetwiseLlmRanker.rerank()      │
│  ├─ heapSort() 或 bubbleSort()          │
│  └─ compare() x 多次                    │
└─────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────┐
│ compare(query, docs)                    │
│  ├─ 构建提示词                           │
│  └─ self.adapter.generate(prompt)       │
└─────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────┐
│ LlmInferenceAdapter.generate()           │
│  ├─ tokenizer.encode(prompt)            │
│  ├─ model.generate(input_ids)           │
│  ├─ tokenizer.decode(output_ids)        │
│  └─ return [output_text]                │
└─────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────┐
│ HuggingFace Model                       │
│  ├─ T5ForConditionalGeneration或        │
│  └─ AutoModelForCausalLM                │
└─────────────────────────────────────────┘
   │
   ▼
最终输出文本
```

## 模型自动选择流程

```
用户: "meta-llama/Llama-2-7b-hf"
   │
   ▼
┌────────────────────────────────────────┐
│ ModelAdapterFactory.create_adapter()   │
│  └─ 检查模型配置                        │
└────────────────────────────────────────┘
   │
   ▼
┌────────────────────────────────────────┐
│ config = AutoConfig.from_pretrained()  │
│ model_type = "llama"                   │
└────────────────────────────────────────┘
   │
   ▼
┌────────────────────────────────────────┐
│ 在 _ADAPTER_MAP 中查找                   │
│ "llama" -> CausalLmAdapter             │
└────────────────────────────────────────┘
   │
   ▼
┌────────────────────────────────────────┐
│ return CausalLmAdapter(...)            │
│  ├─ 初始化tokenizer                     │
│  ├─ 加载模型到GPU                      │
│  └─ 准备好推理                         │
└────────────────────────────────────────┘
   │
   ▼
✓ 准备就绪！
```

## 代码复用对比

### 之前（有大量重复）

```
setwise.py
├─ 模型加载 (T5特定)
├─ 模型加载 (LLaMA特定)
├─ generate逻辑 (T5特定)
├─ generate逻辑 (LLaMA特定)
└─ 其他logic

pairwise.py
├─ 模型加载 (T5特定)  ← 重复
├─ 模型加载 (LLaMA特定)  ← 重复
├─ generate逻辑 (T5特定)  ← 重复
├─ generate逻辑 (LLaMA特定)  ← 重复
└─ 其他logic

listwise.py
├─ 模型加载 (T5特定)  ← 重复
├─ 模型加载 (LLaMA特定)  ← 重复
├─ generate逻辑 (T5特定)  ← 重复
├─ generate逻辑 (LLaMA特定)  ← 重复
└─ 其他logic
```

### 现在（高度复用）

```
model_adapter.py (新增)
├─ T5Adapter
│  ├─ generate()
│  └─ get_logits()
├─ CausalLmAdapter
│  ├─ generate()
│  └─ get_logits()
└─ ModelAdapterFactory

universal_ranker.py (新增)
├─ UniversalLlmRanker (基类)

universal_setwise.py (新增)
├─ UniversalSetwiseLlmRanker
└─ UniversalSetwiseLlmRankerWithVoting

universal_pairwise.py (未来)
└─ UniversalPairwiseLlmRanker

universal_listwise.py (未来)
└─ UniversalListwiseLlmRanker
```

## 扩展性示例

### 添加新模型支持

```
新模型出现 (如 Gemma)
   │
   ▼
检查是否是 Causal LM？
   │
   ├─ 是 ──► 使用 CausalLmAdapter ✓ (自动工作！)
   │
   └─ 否 ──► 创建自定义 GemmaAdapter
                  │
                  ▼
            继承 LlmInferenceAdapter
                  │
                  ▼
            实现 generate() 等方法
                  │
                  ▼
            ModelAdapterFactory.register_adapter()
                  │
                  ▼
            ✓ 完成！所有ranker自动支持
```

## 性能架构

```
┌──────────────────────┐
│   用户请求           │
└──────────┬───────────┘
           │
           ▼
    ┌─────────────────┐
    │ Ranker Layer    │  ← 轻量级，不影响性能
    │ (O(n) 复杂度)   │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────────┐
    │ Model Adapter       │  ← 轻量级包装，
    │ (基本无开销)        │     完全透明
    └────────┬────────────┘
             │
             ▼
    ┌─────────────────────┐
    │ GPU 推理            │  ◄── 性能瓶颈
    │ (主要耗时)          │     完全相同！
    └─────────────────────┘
```

## 支持矩阵

```
┌─────────────────────┬─────────┬──────────────┬────────┐
│ 模型系列            │ 类型    │ 适配器       │ 状态   │
├─────────────────────┼─────────┼──────────────┼────────┤
│ Flan-T5             │ ED*     │ T5Adapter    │ ✓      │
│ T5                  │ ED      │ T5Adapter    │ ✓      │
│ mT5                 │ ED      │ T5Adapter    │ ✓      │
│ LLaMA 2             │ DC**    │ CausalLmA.   │ ✓      │
│ Mistral             │ DC      │ CausalLmA.   │ ✓      │
│ Phi                 │ DC      │ CausalLmA.   │ ✓      │
│ Qwen                │ DC      │ CausalLmA.   │ ✓      │
│ Baichuan            │ DC      │ CausalLmA.   │ ✓      │
│ Falcon              │ DC      │ CausalLmA.   │ ✓      │
│ EleutherAI          │ DC      │ CausalLmA.   │ ✓      │
│ StarCoder           │ DC      │ CausalLmA.   │ ✓      │
│ ...                 │ ...     │ ...          │ ...    │
├─────────────────────┼─────────┼──────────────┼────────┤
│ 总计                │         │ 100+         │ ✓      │
└─────────────────────┴─────────┴──────────────┴────────┘
  *ED = Encoder-Decoder
  **DC = Decoder-Only (Causal LM)
```

---

这个架构确保了：
- ✅ 关注点分离 (Separation of Concerns)
- ✅ 单一职责原则 (Single Responsibility)
- ✅ 开放封闭原则 (Open/Closed)
- ✅ 依赖反转原则 (Dependency Inversion)
