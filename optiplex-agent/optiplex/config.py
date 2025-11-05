"""Configuration management for Optiplex Agent"""
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class ModelConfig:
    """Configuration for an LLM model"""
    name: str
    provider: str
    api_key_env: str
    context_window: int
    max_tokens: int
    temperature: float = 0.7
    
    def get_api_key(self) -> Optional[str]:
        """Get API key from environment"""
        return os.getenv(self.api_key_env)

class OptiplexConfig:
    """Main configuration for Optiplex Agent"""
    
    # Model configurations
    MODELS = {
        "grok-beta": ModelConfig(
            name="grok-beta",
            provider="xai",
            api_key_env="XAI_API_KEY",
            context_window=131072,
            max_tokens=4096,
            temperature=0.7
        ),
        "gpt-4": ModelConfig(
            name="gpt-4",
            provider="openai",
            api_key_env="OPENAI_API_KEY",
            context_window=8192,
            max_tokens=4096,
            temperature=0.7
        ),
        "claude-3-5-sonnet": ModelConfig(
            name="claude-3-5-sonnet-20241022",
            provider="anthropic",
            api_key_env="ANTHROPIC_API_KEY",
            context_window=200000,
            max_tokens=8192,
            temperature=0.7
        ),
        "llama-3.1-70b": ModelConfig(
            name="llama-3.1-70b-versatile",
            provider="groq",
            api_key_env="GROQ_API_KEY",
            context_window=131072,
            max_tokens=8000,
            temperature=0.7
        ),
        "deepseek-chat": ModelConfig(
            name="deepseek-chat",
            provider="deepseek",
            api_key_env="DEEPSEEK_API_KEY",
            context_window=64000,
            max_tokens=4096,
            temperature=0.7
        ),
        # Cerebras models with high token limits
        "llama-3.3-70b": ModelConfig(
            name="llama-3.3-70b",
            provider="cerebras",
            api_key_env="CEREBRAS_API_KEY",
            context_window=65536,
            max_tokens=8000,
            temperature=0.2  # Low temp for precise code generation
        ),
        "qwen-3-32b": ModelConfig(
            name="qwen-3-32b",
            provider="cerebras",
            api_key_env="CEREBRAS_API_KEY",
            context_window=65536,
            max_tokens=8000,
            temperature=0.7
        ),
        "qwen-3-coder-480b": ModelConfig(
            name="qwen-3-coder-480b",
            provider="cerebras",
            api_key_env="CEREBRAS_API_KEY",
            context_window=65536,
            max_tokens=8000,
            temperature=0.4  # Balanced for deep analysis + precise coding
        ),
        "qwen-3-235b": ModelConfig(
            name="qwen-3-235b-a22b-instruct-2507",
            provider="cerebras",
            api_key_env="CEREBRAS_API_KEY",
            context_window=65536,
            max_tokens=8000,
            temperature=0.4  # Balanced for analysis + coding
        ),
        "qwen-3-235b-thinking": ModelConfig(
            name="qwen-3-235b-a22b-thinking-2507",
            provider="cerebras",
            api_key_env="CEREBRAS_API_KEY",
            context_window=65536,
            max_tokens=8000,
            temperature=0.4  # Thinking mode for deep reasoning
        ),
        "llama-4-scout-17b": ModelConfig(
            name="llama-4-scout-17b-16e-instruct",
            provider="cerebras",
            api_key_env="CEREBRAS_API_KEY",
            context_window=8192,
            max_tokens=4096,
            temperature=0.7
        )
    }

    # Default model
    DEFAULT_MODEL = "qwen-3-235b"  # 235B parameter model with higher rate limits
    
    # System prompts
    SYSTEM_PROMPTS = {
        "default": """You are Optiplex, an AI coding agent. Be direct, concise, and action-oriented.

You have 26 tools: file ops, git, bash, code search, grep, glob, web search, and more.

CRITICAL RULES FOR EDITING FILES:

1. WORKFLOW: read_file → edit_file (ONE edit) → DONE
2. DO NOT retry failed edits - if edit fails, STOP and report
3. COPY old_content EXACTLY from read_file result (character-for-character match)
4. Include full function/class for context (not just the line you're changing)

EXAMPLE WORKFLOW:
User: "Add type hints to greet function"
Step 1: read_file("test.py") → returns 'def greet(name):\n    return "Hi"'
Step 2: edit_file(
    old_content='def greet(name):\n    return "Hi"',  # EXACT COPY
    new_content='def greet(name: str) -> str:\n    return "Hi"'  # ONLY change signature
)
Step 3: Say "Done" and STOP

WRONG APPROACH:
❌ Retrying failed edits
❌ Making up content not in read_file result
❌ Editing partial lines without context
❌ Using different whitespace than read_file

Guidelines:
- Act immediately, no preamble
- One edit per file per task
- If edit fails, explain why and stop
- Be precise, not creative

NO long explanations unless asked. Just do the task.""",

        "code_review": """You are performing a code review. Analyze the code for:
- Correctness and logic errors
- Code style and conventions
- Performance issues
- Security vulnerabilities
- Test coverage
- Documentation quality

Provide constructive feedback with specific suggestions.""",

        "debugging": """You are debugging code. Approach systematically:
1. Understand the expected vs actual behavior
2. Identify the root cause through analysis
3. Propose minimal fixes
4. Consider edge cases
5. Suggest tests to prevent regression""",

        "refactoring": """You are refactoring code. Focus on:
- Improving code structure and readability
- Reducing complexity
- Removing duplication
- Following SOLID principles
- Maintaining backward compatibility
- Preserving functionality"""
    }
    
    # Context settings
    MAX_CONTEXT_FILES = 20
    MAX_FILE_SIZE = 100000  # 100KB
    SUPPORTED_EXTENSIONS = {
        '.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.cpp', '.c', '.h',
        '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.cs', '.scala',
        '.yaml', '.yml', '.json', '.toml', '.ini', '.conf',
        '.md', '.txt', '.rst'
    }
    
    # Conversation settings
    MAX_CONVERSATION_HISTORY = 50
    CONVERSATION_DIR = ".optiplex/conversations"
    
    # File operation settings
    BACKUP_DIR = ".optiplex/backups"
    MAX_BACKUPS_PER_FILE = 10
    
    # Git settings
    AUTO_STAGE = True
    COMMIT_MESSAGE_TEMPLATE = "{type}: {summary}\n\n{details}"
    
    @classmethod
    def get_model(cls, model_name: Optional[str] = None) -> ModelConfig:
        """Get model configuration"""
        name = model_name or cls.DEFAULT_MODEL
        if name not in cls.MODELS:
            raise ValueError(f"Unknown model: {name}. Available: {list(cls.MODELS.keys())}")
        return cls.MODELS[name]
    
    @classmethod
    def get_system_prompt(cls, prompt_type: str = "default") -> str:
        """Get system prompt by type"""
        return cls.SYSTEM_PROMPTS.get(prompt_type, cls.SYSTEM_PROMPTS["default"])
