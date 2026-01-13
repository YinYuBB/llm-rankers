"""
Universal Ranking Base Classes using Model Adapter
Simplified to work with any HuggingFace LLM model
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional
from .model_adapter import LlmInferenceAdapter, ModelAdapterFactory


@dataclass
class SearchResult:
    docid: str
    score: float
    text: Optional[str] = None


class UniversalLlmRanker:
    """Universal base class for LLM-based rankers using any model"""
    
    def __init__(self, model_name_or_path: str,
                 tokenizer_name_or_path: Optional[str] = None,
                 device: str = 'cuda',
                 cache_dir: Optional[str] = None,
                 adapter_type: Optional[str] = None,
                 **adapter_kwargs):
        """
        Initialize universal ranker with any HuggingFace model
        
        Args:
            model_name_or_path: Model name or path
            tokenizer_name_or_path: Optional custom tokenizer
            device: 'cuda' or 'cpu'
            cache_dir: Cache directory for models
            adapter_type: Force specific adapter ('t5' or 'causal_lm'). Auto-detect if None
            **adapter_kwargs: Additional kwargs passed to adapter
        """
        self.adapter = ModelAdapterFactory.create_adapter(
            model_name_or_path=model_name_or_path,
            tokenizer_name_or_path=tokenizer_name_or_path,
            device=device,
            cache_dir=cache_dir,
            adapter_type=adapter_type
        )
        
        self.device = device
        self.total_compare = 0
        self.total_completion_tokens = 0
        self.total_prompt_tokens = 0
    
    def rerank(self, query: str, ranking: List[SearchResult]) -> List[SearchResult]:
        """Override this method in subclasses"""
        raise NotImplementedError
    
    def truncate(self, text: str, length: int) -> str:
        """Truncate text to max tokens"""
        tokens = self.adapter.tokenizer.tokenize(text)
        return self.adapter.tokenizer.convert_tokens_to_string(tokens[:length])
    
    @property
    def model_type(self) -> str:
        return self.adapter.model_type


# Export original SearchResult for backward compatibility
__all__ = ['SearchResult', 'UniversalLlmRanker', 'LlmInferenceAdapter', 'ModelAdapterFactory']
