"""
Model Adapter Layer - Abstracts different LLM models for ranking tasks
Supports any HuggingFace model with a unified inference interface
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import torch
from transformers import AutoTokenizer, AutoConfig, AutoModelForCausalLM, T5ForConditionalGeneration, T5Tokenizer
import re


class LlmInferenceAdapter(ABC):
    """Base class for LLM inference adapters"""
    
    def __init__(self, model_name_or_path: str, tokenizer_name_or_path: Optional[str] = None, 
                 device: str = 'cuda', cache_dir: Optional[str] = None):
        self.model_name_or_path = model_name_or_path
        self.tokenizer_name_or_path = tokenizer_name_or_path or model_name_or_path
        self.device = device
        self.cache_dir = cache_dir
        
        self.config = AutoConfig.from_pretrained(model_name_or_path, cache_dir=cache_dir)
        self.tokenizer = None
        self.model = None
        self._init_model()
        
    @abstractmethod
    def _init_model(self):
        """Initialize tokenizer and model"""
        pass
    
    @abstractmethod
    def generate(self, prompts: List[str], **kwargs) -> List[str]:
        """Generate text from prompts. Returns list of generated texts"""
        pass
    
    @abstractmethod
    def get_logits(self, input_ids: torch.Tensor) -> torch.Tensor:
        """Get logits from input_ids (for likelihood-based scoring)"""
        pass
    
    def batch_generate(self, prompts: List[str], batch_size: int = 1, **kwargs) -> List[str]:
        """Generate text for a list of prompts with batching"""
        results = []
        for i in range(0, len(prompts), batch_size):
            batch_prompts = prompts[i:i+batch_size]
            results.extend(self.generate(batch_prompts, **kwargs))
        return results
    
    @property
    def model_type(self) -> str:
        """Return model type"""
        return getattr(self.config, 'model_type', 'unknown')


class T5Adapter(LlmInferenceAdapter):
    """Adapter for T5-based models"""
    
    def _init_model(self):
        self.tokenizer = T5Tokenizer.from_pretrained(self.tokenizer_name_or_path, cache_dir=self.cache_dir)
        self.model = T5ForConditionalGeneration.from_pretrained(
            self.model_name_or_path,
            device_map='auto',
            torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32,
            cache_dir=self.cache_dir
        )
        self.decoder_input_ids = self.tokenizer.encode(
            "<pad> Passage",
            return_tensors="pt",
            add_special_tokens=False
        ).to(self.model.device)
    
    def generate(self, prompts: List[str], max_new_tokens: int = 2, **kwargs) -> List[str]:
        """Generate using T5 encoder-decoder"""
        if isinstance(prompts, str):
            prompts = [prompts]
            
        input_ids = self.tokenizer(prompts, return_tensors="pt", padding=True).input_ids.to(self.model.device)
        
        decoder_input_ids = self.decoder_input_ids.repeat(len(prompts), 1)
        output_ids = self.model.generate(
            input_ids,
            decoder_input_ids=decoder_input_ids,
            max_new_tokens=max_new_tokens,
            **kwargs
        )
        
        outputs = self.tokenizer.batch_decode(output_ids, skip_special_tokens=True)
        return outputs
    
    def get_logits(self, input_ids: torch.Tensor) -> torch.Tensor:
        """Get logits for T5 model"""
        with torch.no_grad():
            logits = self.model(input_ids=input_ids, decoder_input_ids=self.decoder_input_ids).logits
        return logits


class CausalLmAdapter(LlmInferenceAdapter):
    """Adapter for Causal Language Models (LLaMA, Mistral, Phi, etc.)"""
    
    def _init_model(self):
        self.tokenizer = AutoTokenizer.from_pretrained(self.tokenizer_name_or_path, cache_dir=self.cache_dir)
        
        # Set default pad token if not set
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        self.tokenizer.padding_side = "left"
        
        # Special handling for specific models
        if 'vicuna' in self.model_name_or_path.lower() and 'v1.5' in self.model_name_or_path:
            self.tokenizer.use_default_system_prompt = False
            self.tokenizer.chat_template = (
                "{% if messages[0]['role'] == 'system' %}"
                "{% set loop_messages = messages[1:] %}"
                "{% set system_message = messages[0]['content'] %}"
                "{% else %}"
                "{% set loop_messages = messages %}"
                "{% set system_message = 'A chat between a curious user and an artificial intelligence assistant. "
                "The assistant gives helpful, detailed, and polite answers to the user\\'s questions.' %}"
                "{% endif %}"
                "{% for message in loop_messages %}"
                "{% if (message['role'] == 'user') != (loop.index0 % 2 == 0) %}"
                "{{ raise_exception('Conversation roles must alternate user/assistant/user/assistant/...') }}"
                "{% endif %}"
                "{% if loop.index0 == 0 %}{{ system_message }}{% endif %}"
                "{% if message['role'] == 'user' %}{{ ' USER: ' + message['content'].strip() }}"
                "{% elif message['role'] == 'assistant' %}{{ ' ASSISTANT: ' + message['content'].strip() + eos_token }}"
                "{% endif %}"
                "{% endfor %}"
                "{% if add_generation_prompt %}{{ ' ASSISTANT:' }}{% endif %}"
            )
        
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name_or_path,
            device_map='auto',
            torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32,
            cache_dir=self.cache_dir
        ).eval()
    
    def generate(self, prompts: List[str], max_new_tokens: int = 1, 
                 use_chat_template: bool = False, **kwargs) -> List[str]:
        """Generate using Causal LM"""
        if isinstance(prompts, str):
            prompts = [prompts]
        
        if use_chat_template and hasattr(self.tokenizer, 'apply_chat_template'):
            # Apply chat template if available
            formatted_prompts = []
            for prompt in prompts:
                if isinstance(prompt, list):  # Already a message list
                    formatted_prompts.append(
                        self.tokenizer.apply_chat_template(prompt, tokenize=False, add_generation_prompt=True)
                    )
                else:
                    formatted_prompts.append(prompt)
            prompts = formatted_prompts
        
        input_ids = self.tokenizer(prompts, return_tensors="pt", padding=True).input_ids.to(self.model.device)
        
        output_ids = self.model.generate(
            input_ids,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=0.0,
            **kwargs
        )
        
        # Remove input tokens from output
        generated_ids = output_ids[:, input_ids.shape[1]:]
        outputs = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)
        
        return outputs
    
    def get_logits(self, input_ids: torch.Tensor) -> torch.Tensor:
        """Get logits for Causal LM"""
        with torch.no_grad():
            logits = self.model(input_ids=input_ids).logits[:, -1, :]
        return logits


class ModelAdapterFactory:
    """Factory for creating appropriate model adapters"""
    
    _ADAPTER_MAP = {
        't5': T5Adapter,
        'llama': CausalLmAdapter,
        'gpt2': CausalLmAdapter,
        'gpt_neox': CausalLmAdapter,  # EleutherAI models
        'mistral': CausalLmAdapter,
        'phi': CausalLmAdapter,
        'qwen': CausalLmAdapter,
        'baichuan': CausalLmAdapter,
        'bloom': CausalLmAdapter,
        'falcon': CausalLmAdapter,
        'mpt': CausalLmAdapter,
        'stablelm': CausalLmAdapter,
        'opt': CausalLmAdapter,
        'gpt_bigcode': CausalLmAdapter,  # Code models
    }
    
    @classmethod
    def create_adapter(cls, model_name_or_path: str, 
                      tokenizer_name_or_path: Optional[str] = None,
                      device: str = 'cuda', 
                      cache_dir: Optional[str] = None,
                      adapter_type: Optional[str] = None) -> LlmInferenceAdapter:
        """
        Create appropriate adapter for a model
        
        Args:
            model_name_or_path: Model name or path
            tokenizer_name_or_path: Tokenizer name or path (optional)
            device: Device to use ('cuda' or 'cpu')
            cache_dir: Cache directory for models
            adapter_type: Force specific adapter type (optional, auto-detect if not provided)
        
        Returns:
            LlmInferenceAdapter instance
        """
        config = AutoConfig.from_pretrained(model_name_or_path, cache_dir=cache_dir, trust_remote_code=True)
        model_type = getattr(config, 'model_type', 'unknown').lower()
        
        # Use forced adapter type if provided
        if adapter_type:
            adapter_class = cls._ADAPTER_MAP.get(adapter_type.lower())
        else:
            adapter_class = cls._ADAPTER_MAP.get(model_type)
        
        if adapter_class is None:
            # Default to CausalLmAdapter for unknown types
            print(f"Warning: Model type '{model_type}' not explicitly supported. Attempting CausalLmAdapter...")
            adapter_class = CausalLmAdapter
        
        return adapter_class(model_name_or_path, tokenizer_name_or_path, device, cache_dir)
    
    @classmethod
    def register_adapter(cls, model_type: str, adapter_class: type):
        """Register a new adapter for a model type"""
        cls._ADAPTER_MAP[model_type.lower()] = adapter_class
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """Get list of supported model types"""
        return list(cls._ADAPTER_MAP.keys())
