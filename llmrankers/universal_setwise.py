"""
Universal Setwise Ranker - Works with any HuggingFace LLM
Simplified version using the model adapter layer
"""

from typing import List, Optional
import copy
import torch
import random
from collections import Counter
from .universal_ranker import SearchResult, UniversalLlmRanker
from .model_adapter import LlmInferenceAdapter

random.seed(929)


class UniversalSetwiseLlmRanker(UniversalLlmRanker):
    """
    Universal Setwise Ranker that works with any HuggingFace LLM
    
    Usage:
        # Works with ANY HuggingFace model!
        ranker = UniversalSetwiseLlmRanker(
            model_name_or_path="meta-llama/Llama-2-7b-hf",
            # or: "google/flan-t5-large"
            # or: "mistralai/Mistral-7B-Instruct-v0.1"
            # or: "microsoft/phi-2"
            device='cuda'
        )
    """
    
    CHARACTERS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L",
                  "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W"]
    
    def __init__(self, 
                 model_name_or_path: str,
                 tokenizer_name_or_path: Optional[str] = None,
                 device: str = 'cuda',
                 num_child: int = 3,
                 k: int = 10,
                 method: str = "heapsort",
                 cache_dir: Optional[str] = None,
                 **kwargs):
        """
        Args:
            model_name_or_path: Any HuggingFace model (T5, LLaMA, Mistral, etc.)
            tokenizer_name_or_path: Optional custom tokenizer
            device: 'cuda' or 'cpu'
            num_child: Number of children in heap sort
            k: Number of top documents to return
            method: 'heapsort' or 'bubblesort'
            cache_dir: Cache directory for models
        """
        super().__init__(
            model_name_or_path=model_name_or_path,
            tokenizer_name_or_path=tokenizer_name_or_path,
            device=device,
            cache_dir=cache_dir
        )
        
        self.num_child = num_child
        self.k = k
        self.method = method
        
        print(f"✓ Initialized UniversalSetwiseLlmRanker with {self.adapter.model_type} model")
    
    def compare(self, query: str, docs: List[SearchResult]) -> str:
        """
        Compare documents and return the most relevant one
        Works with both encoder-decoder (T5) and decoder-only (LLaMA, etc.) models
        """
        self.total_compare += 1
        
        passages = "\n\n".join([f'Passage {self.CHARACTERS[i]}: "{doc.text}"' 
                               for i, doc in enumerate(docs)])
        
        prompt = (f'Given a query "{query}", which of the following passages is the most '
                 f'relevant one to the query?\n\n{passages}\n\n'
                 f'Output only the passage label of the most relevant passage:')
        
        # Generate using adapter (works for any model type)
        outputs = self.adapter.generate([prompt], max_new_tokens=2)
        output = outputs[0].strip()
        
        # Extract passage label
        if len(output) > 0:
            # Try to extract letter from output
            for char in output.upper():
                if char in self.CHARACTERS:
                    return char
        
        print(f"Warning: Unexpected output format: {output}")
        return "A"  # Default fallback
    
    def heapify(self, arr: List[SearchResult], n: int, i: int, query: str):
        """Heapify operation for heap sort"""
        if self.num_child * i + 1 < n:
            docs = [arr[i]] + arr[self.num_child * i + 1: min((self.num_child * (i + 1) + 1), n)]
            inds = [i] + list(range(self.num_child * i + 1, min((self.num_child * (i + 1) + 1), n)))
            
            output = self.compare(query, docs)
            try:
                best_ind = self.CHARACTERS.index(output)
            except ValueError:
                best_ind = 0
            
            try:
                largest = inds[best_ind]
            except IndexError:
                largest = i
            
            if largest != i:
                arr[i], arr[largest] = arr[largest], arr[i]
                self.heapify(arr, n, largest, query)
    
    def heapSort(self, arr: List[SearchResult], query: str, k: int):
        """Heap sort implementation"""
        n = len(arr)
        ranked = 0
        
        # Build max heap
        for i in range(n // self.num_child, -1, -1):
            self.heapify(arr, n, i, query)
        
        # Extract k elements
        for i in range(n - 1, 0, -1):
            arr[i], arr[0] = arr[0], arr[i]
            ranked += 1
            if ranked == k:
                break
            self.heapify(arr, i, 0, query)
    
    def rerank(self, query: str, ranking: List[SearchResult]) -> List[SearchResult]:
        """
        Rerank documents using setwise comparison
        Works with any HuggingFace model!
        """
        original_ranking = copy.deepcopy(ranking)
        self.total_compare = 0
        
        if self.method == "heapsort":
            self.heapSort(ranking, query, self.k)
            ranking = list(reversed(ranking))
        elif self.method == "bubblesort":
            raise NotImplementedError("Bubblesort not implemented in universal version yet")
        else:
            raise NotImplementedError(f'Method {self.method} is not implemented.')
        
        # Create results with original full text
        results = []
        top_doc_ids = set()
        rank = 1
        
        for doc in ranking[:self.k]:
            top_doc_ids.add(doc.docid)
            results.append(SearchResult(docid=doc.docid, score=-rank, text=None))
            rank += 1
        
        for doc in original_ranking:
            if doc.docid not in top_doc_ids:
                results.append(SearchResult(docid=doc.docid, score=-rank, text=None))
                rank += 1
        
        return results


class UniversalSetwiseLlmRankerWithVoting(UniversalSetwiseLlmRanker):
    """
    Extended version with multiple permutations and voting
    More robust but slower
    """
    
    def __init__(self, 
                 model_name_or_path: str,
                 tokenizer_name_or_path: Optional[str] = None,
                 device: str = 'cuda',
                 num_child: int = 3,
                 k: int = 10,
                 method: str = "heapsort",
                 num_permutation: int = 1,
                 cache_dir: Optional[str] = None):
        """
        Args:
            num_permutation: Number of random permutations for voting (1 = no voting)
        """
        super().__init__(
            model_name_or_path=model_name_or_path,
            tokenizer_name_or_path=tokenizer_name_or_path,
            device=device,
            num_child=num_child,
            k=k,
            method=method,
            cache_dir=cache_dir
        )
        self.num_permutation = num_permutation
    
    def compare(self, query: str, docs: List[SearchResult]) -> str:
        """Compare with voting if num_permutation > 1"""
        if self.num_permutation == 1:
            return super().compare(query, docs)
        
        # Multiple permutations with voting
        self.total_compare += self.num_permutation
        
        candidates = []
        for _ in range(self.num_permutation):
            # Random permutation
            permuted_docs = random.sample(docs, len(docs))
            permuted_chars = random.sample(self.CHARACTERS[:len(docs)], len(docs))
            
            # Create passage string
            passages = "\n\n".join([f'Passage {permuted_chars[i]}: "{permuted_docs[i].text}"' 
                                   for i in range(len(permuted_docs))])
            
            prompt = (f'Given a query "{query}", which of the following passages is the most '
                     f'relevant one to the query?\n\n{passages}\n\n'
                     f'Output only the passage label of the most relevant passage:')
            
            output = self.adapter.generate([prompt], max_new_tokens=2)[0].strip().upper()
            
            # Track which original doc won
            try:
                idx_in_permuted = permuted_chars.index(output)
                original_doc_idx = docs.index(permuted_docs[idx_in_permuted])
                candidates.append(original_doc_idx)
            except (ValueError, IndexError):
                pass
        
        # Voting
        if candidates:
            candidate_counts = Counter(candidates)
            max_count = max(candidate_counts.values())
            winners = [c for c, count in candidate_counts.items() if count == max_count]
            winner_idx = random.choice(winners)
            return self.CHARACTERS[winner_idx]
        
        return "A"


# Example usage in docstring
__doc__ += """

Example Usage:
==============

# Works with T5 models
ranker = UniversalSetwiseLlmRanker("google/flan-t5-large")

# Works with LLaMA
ranker = UniversalSetwiseLlmRanker("meta-llama/Llama-2-7b-hf")

# Works with Mistral
ranker = UniversalSetwiseLlmRanker("mistralai/Mistral-7B-Instruct-v0.1")

# Works with Phi
ranker = UniversalSetwiseLlmRanker("microsoft/phi-2")

# With voting for more robustness
ranker = UniversalSetwiseLlmRankerWithVoting(
    model_name_or_path="google/flan-t5-large",
    num_permutation=3  # Vote from 3 random permutations
)

# Rerank documents
results = ranker.rerank(query="machine learning", ranking=ranking_list)
"""
