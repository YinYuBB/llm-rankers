#!/usr/bin/env python3
"""
完整示例：使用通用Ranker支持任何HuggingFace模型

这个例子展示如何：
1. 用不同的模型初始化ranker
2. 执行重排序
3. 比较不同模型的效果
"""

from llmrankers.universal_setwise import UniversalSetwiseLlmRanker, UniversalSetwiseLlmRankerWithVoting
from llmrankers.universal_ranker import SearchResult


def create_sample_ranking():
    """创建示例排序结果"""
    docs = [
        SearchResult(docid="1", score=10, text="Machine learning is a subset of artificial intelligence."),
        SearchResult(docid="2", score=9, text="Deep learning uses neural networks with multiple layers."),
        SearchResult(docid="3", score=8, text="Natural language processing helps computers understand text."),
        SearchResult(docid="4", score=7, text="Computer vision enables machines to interpret visual content."),
        SearchResult(docid="5", score=6, text="Reinforcement learning trains agents through reward signals."),
    ]
    return docs


def example_1_t5_model():
    """示例1：使用T5模型"""
    print("\n" + "="*60)
    print("示例1：使用Flan-T5模型")
    print("="*60)
    
    ranker = UniversalSetwiseLlmRanker(
        model_name_or_path="google/flan-t5-base",
        device="cuda",
        k=3
    )
    
    query = "machine learning techniques"
    ranking = create_sample_ranking()
    
    print(f"Query: {query}")
    print(f"\nOriginal ranking:")
    for i, doc in enumerate(ranking):
        print(f"  {i+1}. [{doc.docid}] {doc.text}")
    
    results = ranker.rerank(query, ranking)
    
    print(f"\nReranked (top-3):")
    for i, doc in enumerate(results[:3]):
        print(f"  {i+1}. [{doc.docid}] Score: {doc.score}")


def example_2_llama_model():
    """示例2：使用LLaMA模型"""
    print("\n" + "="*60)
    print("示例2：使用LLaMA-2-7B模型")
    print("="*60)
    
    ranker = UniversalSetwiseLlmRanker(
        model_name_or_path="meta-llama/Llama-2-7b-hf",
        device="cuda",
        k=3,
        num_child=2
    )
    
    query = "neural networks and deep learning"
    ranking = create_sample_ranking()
    
    print(f"Query: {query}")
    results = ranker.rerank(query, ranking)
    
    print(f"Reranked results:")
    for i, doc in enumerate(results[:3]):
        print(f"  {i+1}. [{doc.docid}] Score: {doc.score}")


def example_3_voting_ranker():
    """示例3：使用投票机制的Ranker（更稳健）"""
    print("\n" + "="*60)
    print("示例3：投票机制Ranker（3次排列投票）")
    print("="*60)
    
    ranker = UniversalSetwiseLlmRankerWithVoting(
        model_name_or_path="google/flan-t5-base",
        num_permutation=3,  # 3次随机排列
        k=3,
        device="cuda"
    )
    
    query = "AI and machine learning"
    ranking = create_sample_ranking()
    
    print(f"Query: {query}")
    print(f"Running 3 permutations for voting...")
    
    results = ranker.rerank(query, ranking)
    
    print(f"Reranked results (voted):")
    for i, doc in enumerate(results[:3]):
        print(f"  {i+1}. [{doc.docid}] Score: {doc.score}")
    
    print(f"\nTotal comparisons: {ranker.total_compare}")


def example_4_model_comparison():
    """示例4：比较不同模型的结果"""
    print("\n" + "="*60)
    print("示例4：模型对比")
    print("="*60)
    
    models = [
        "google/flan-t5-base",
        "google/flan-t5-large",
    ]
    
    query = "machine learning and AI"
    ranking = create_sample_ranking()
    
    print(f"Query: {query}\n")
    
    for model_name in models:
        print(f"\nModel: {model_name}")
        print("-" * 40)
        
        try:
            ranker = UniversalSetwiseLlmRanker(
                model_name_or_path=model_name,
                device="cuda",
                k=2
            )
            
            results = ranker.rerank(query, ranking)
            
            for i, doc in enumerate(results[:2]):
                print(f"  {i+1}. [{doc.docid}] Score: {doc.score}")
            
            print(f"  Total comparisons: {ranker.total_compare}")
        except Exception as e:
            print(f"  Error: {e}")


def example_5_custom_prompts():
    """示例5：自定义Ranker类以修改提示词"""
    print("\n" + "="*60)
    print("示例5：自定义提示词的Ranker")
    print("="*60)
    
    class CustomPromptSetwiseLlmRanker(UniversalSetwiseLlmRanker):
        """自定义提示词的Ranker"""
        
        def compare(self, query: str, docs):
            """重写compare方法以使用自定义提示词"""
            self.total_compare += 1
            
            passages = "\n\n".join([
                f'[{self.CHARACTERS[i]}] {doc.text}' 
                for i, doc in enumerate(docs)
            ])
            
            # 自定义提示词
            prompt = f"""
任务：给定查询和一些段落，选择最相关的段落。

查询：{query}

段落：
{passages}

请回复最相关段落的标签（仅回复字母，如：A）：
"""
            
            outputs = self.adapter.generate([prompt], max_new_tokens=2)
            output = outputs[0].strip().upper()
            
            # 提取标签
            for char in output:
                if char in self.CHARACTERS:
                    return char
            
            return "A"
    
    ranker = CustomPromptSetwiseLlmRanker(
        model_name_or_path="google/flan-t5-base",
        device="cuda",
        k=2
    )
    
    query = "what is machine learning?"
    ranking = create_sample_ranking()
    
    print(f"Query: {query}")
    results = ranker.rerank(query, ranking)
    
    print(f"\nResults:")
    for i, doc in enumerate(results[:2]):
        print(f"  {i+1}. [{doc.docid}]")


def example_6_batch_ranking():
    """示例6：批量处理多个查询"""
    print("\n" + "="*60)
    print("示例6：批量处理多个查询")
    print("="*60)
    
    ranker = UniversalSetwiseLlmRanker(
        model_name_or_path="google/flan-t5-base",
        device="cuda",
        k=2
    )
    
    queries = [
        "deep learning neural networks",
        "natural language processing",
        "computer vision"
    ]
    
    for query in queries:
        ranking = create_sample_ranking()
        results = ranker.rerank(query, ranking)
        
        print(f"\nQuery: {query}")
        for i, doc in enumerate(results[:2]):
            print(f"  {i+1}. [{doc.docid}]")


def example_7_supported_models():
    """示例7：列出支持的模型类型"""
    print("\n" + "="*60)
    print("示例7：支持的模型类型")
    print("="*60)
    
    from llmrankers.model_adapter import ModelAdapterFactory
    
    supported = ModelAdapterFactory.get_supported_types()
    
    print("\n支持的模型类型（可自动检测）:")
    for model_type in sorted(supported):
        print(f"  • {model_type}")
    
    print("\n可使用的HuggingFace模型示例:")
    examples = {
        "T5系列": [
            "google/flan-t5-base",
            "google/flan-t5-large",
            "google/t5-base",
        ],
        "LLaMA系列": [
            "meta-llama/Llama-2-7b-chat-hf",
            "meta-llama/Llama-2-13b-chat-hf",
            "meta-llama/Llama-2-70b-chat-hf",
        ],
        "Mistral系列": [
            "mistralai/Mistral-7B-Instruct-v0.1",
            "mistralai/Mistral-7B-v0.1",
        ],
        "其他": [
            "microsoft/phi-2",
            "Qwen/Qwen-7B-Chat",
            "EleutherAI/pythia-12b",
        ]
    }
    
    for category, models in examples.items():
        print(f"\n{category}:")
        for model in models:
            print(f"  • {model}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("通用Ranker完整示例")
    print("支持HuggingFace上的所有LLM模型！")
    print("="*60)
    
    # 运行示例（取消注释要运行的示例）
    
    # example_1_t5_model()
    # example_2_llama_model()
    # example_3_voting_ranker()
    # example_4_model_comparison()
    # example_5_custom_prompts()
    # example_6_batch_ranking()
    example_7_supported_models()
    
    print("\n" + "="*60)
    print("✓ 所有示例完成")
    print("="*60)
