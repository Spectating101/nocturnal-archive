"""
FinGPT model loader with LoRA support and 4-bit quantization
"""
from __future__ import annotations
import os
import json
from typing import Dict, Optional

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    from peft import PeftModel
    from src.config.settings import get_settings
    HAS_FINGPT_DEPS = True
except ImportError:
    # Use mock implementation if dependencies not available
    from .mock_loader import MockFinGPTModel
    HAS_FINGPT_DEPS = False

if HAS_FINGPT_DEPS:
    logger = get_settings().log_level

    def _load_kwargs_4bit() -> Dict:
        """Get model loading kwargs with 4-bit quantization if available"""
        settings = get_settings()
        
        if settings.fingpt_load_4bit and torch.cuda.is_available():
            try:
                import bitsandbytes as bnb  # noqa
                return dict(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                    device_map="auto",
                )
            except Exception:
                pass
        
        # CPU or no bnb → fp16 on GPU or fp32 on CPU
        return dict(
            torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
        )

    class FinGPTModel:
        """FinGPT model loader with LoRA adapter support"""
        
        _tok: Optional[AutoTokenizer] = None
        _model: Optional[PeftModel] = None
        _adapter_id: Optional[str] = None

        @classmethod
        def load(cls) -> None:
            """Load the FinGPT model with LoRA adapter"""
            if cls._model is not None:
                return
                
            settings = get_settings()
            auth = {"use_auth_token": settings.hf_token} if settings.hf_token else {}
            kwargs = _load_kwargs_4bit()
            
            try:
                # Load tokenizer
                cls._tok = AutoTokenizer.from_pretrained(
                    settings.fingpt_base_model, 
                    **auth, 
                    use_fast=True
                )
                
                # Load base model
                base = AutoModelForCausalLM.from_pretrained(
                    settings.fingpt_base_model, 
                    **auth, 
                    **kwargs
                )
                
                # Attach LoRA adapter
                cls._model = PeftModel.from_pretrained(base, settings.fingpt_lora_id, **auth)
                cls._adapter_id = settings.fingpt_lora_id
                
                # Set pad token if not present
                if cls._tok.pad_token is None:
                    cls._tok.pad_token = cls._tok.eos_token
                    
                cls._model.eval()
                
                print(f"FinGPT model loaded successfully: {settings.fingpt_base_model} + {settings.fingpt_lora_id}")
                
            except Exception as e:
                print(f"Error loading FinGPT model: {e}")
                raise

        @classmethod
        def generate_json(cls, instruction: str, text: str) -> Dict:
            """Generate JSON response for sentiment analysis"""
            cls.load()
            
            if cls._model is None or cls._tok is None:
                raise RuntimeError("Model not loaded")
                
            settings = get_settings()
            
            prompt = (
                "You are a financial NLP assistant. "
                "Return STRICT JSON with keys: label (positive|negative|neutral), score [0..1], rationale (short). "
                "Text:\n"
            )
            prompt += text.strip()
            prompt += "\nInstruction: " + instruction.strip()
            
            # Tokenize input
            ids = cls._tok(
                prompt, 
                return_tensors="pt", 
                truncation=True, 
                max_length=2048
            )
            
            # Move to device
            device = next(cls._model.parameters()).device
            ids = {k: v.to(device) for k, v in ids.items()}
            
            # Generate response
            with torch.no_grad():
                out = cls._model.generate(
                    **ids,
                    max_new_tokens=settings.nlp_max_new_tokens,
                    do_sample=True,
                    temperature=settings.nlp_temperature,
                    eos_token_id=cls._tok.eos_token_id,
                    pad_token_id=cls._tok.eos_token_id,
                )
            
            # Decode response
            raw = cls._tok.decode(out[0], skip_special_tokens=True)
            
            # Extract JSON from response
            jstart = raw.rfind("{")
            jend = raw.rfind("}") + 1
            
            try:
                if jstart >= 0 and jend > jstart:
                    json_str = raw[jstart:jend]
                    return json.loads(json_str)
                else:
                    raise ValueError("No JSON found in response")
            except Exception as e:
                print(f"JSON parse failed: {e}")
                print(f"Raw response: {raw}")
                # Fallback: naive classification heuristic
                text_lower = text.lower()
                if any(word in text_lower for word in ["beat", "exceed", "strong", "growth", "positive", "up", "rise"]):
                    return {"label": "positive", "score": 0.7, "rationale": "fallback: positive keywords detected"}
                elif any(word in text_lower for word in ["miss", "decline", "weak", "negative", "down", "fall", "drop"]):
                    return {"label": "negative", "score": 0.3, "rationale": "fallback: negative keywords detected"}
                else:
                    return {"label": "neutral", "score": 0.5, "rationale": "fallback: no clear sentiment indicators"}

else:
    # Use mock implementation
    FinGPTModel = MockFinGPTModel