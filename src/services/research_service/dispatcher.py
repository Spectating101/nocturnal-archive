import asyncio
from typing import Tuple, List, Dict, Optional
from src.services.llm_service.llm_manager import LLMManager
import os

# Helper: LLM-based intent detection
async def detect_intent_llm(llm_manager: LLMManager, user_message: str, history: List[Dict], user_profile: Optional[Dict] = None) -> Dict:
    prompt = (
        "You are an intent classifier for a research assistant. "
        "Given the user's latest message and conversation history, classify the intent as one of: 'quick_web', 'deep_web', 'academic', or 'clarification'. "
        "Also, classify the topic as 'academic', 'practical', or 'general'. "
        "If the user is following up for more detail, set 'escalate' to true. "
        "Return a JSON object with fields: intent, topic_type, escalate, reason.\n"
        f"User message: {user_message}\n"
        f"History: {history[-5:] if history else []}\n"
        f"User profile: {user_profile or {}}\n"
    )
    # Use LLMManager to get classification
    result = await llm_manager.model_dispatcher.dispatch_document({
        'id': 'intent-detect',
        'title': 'Intent Detection',
        'content': prompt
    }, is_critical=False)
    try:
        parsed = result.get('raw_json') or result.get('raw_text') or result.get('content')
        if isinstance(parsed, str):
            import json
            parsed = json.loads(parsed)
        return parsed
    except Exception:
        return {'intent': 'quick_web', 'topic_type': 'general', 'escalate': False, 'reason': 'fallback'}

async def select_research_engine(user_message: str, history: List[Dict], user_profile: Optional[Dict] = None, llm_manager: Optional[LLMManager] = None) -> Tuple[str, Dict]:
    """
    Nuanced dispatcher: selects research engine based on LLM intent detection, topic, conversation state, and user profile.
    Returns (engine_name, { 'summary': ..., 'citations': [...] })
    """
    # Use LLMManager for intent detection if available
    if llm_manager is None:
        redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
        llm_manager = LLMManager(redis_url)
    intent_info = await detect_intent_llm(llm_manager, user_message, history, user_profile)
    intent = intent_info.get('intent', 'quick_web')
    topic_type = intent_info.get('topic_type', 'general')
    escalate = intent_info.get('escalate', False)
    reason = intent_info.get('reason', '')

    # Escalation: if user is following up for more detail, escalate engine
    if escalate or (intent == 'deep_web' and topic_type == 'academic'):
        intent = 'academic'

    # User profile override
    if user_profile and user_profile.get('prefers_academic'):
        intent = 'academic'
    elif user_profile and user_profile.get('prefers_quick'):
        intent = 'quick_web'

    # Engine selection with parallel web search integration
    if intent == 'academic':
        # Academic research engine - for when user explicitly wants deep research
        from src.services.research_service.context_manager import ResearchContextManager
        return ("academic", { 'summary': "[Academic research will be conducted]", 'citations': [] })
    elif intent == 'deep_web':
        # Web deep research engine - for thorough web investigation
        from src.services.search_service.search_engine import SearchEngine
        return ("web_deep", { 'summary': "[Deep web research will be conducted]", 'citations': [] })
    elif intent == 'clarification':
        # Ask for clarification
        return ("clarification", { 'summary': "Could you clarify your research question or provide more details?", 'citations': [] })
    else:
        # Quick web context (surface) - for parallel background learning
        from src.services.search_service.search_engine import SearchEngine
        return ("web_context", { 'summary': "[Parallel web context gathered]", 'citations': [] })

async def create_projection(user_message: str, history: List[Dict], web_context: List[Dict], llm_manager: Optional[LLMManager] = None) -> str:
    """
    Create a projection of likely research findings based on context and web searches.
    """
    if llm_manager is None:
        redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
        llm_manager = LLMManager(redis_url)
    
    # Combine conversation context and web search results
    context_summary = "\n".join([f"{turn['role']}: {turn['content']}" for turn in history[-5:]])
    web_context_summary = "\n".join([f"- {r.get('title', '')}: {r.get('snippet', '')}" 
                                   for r in web_context[:5]])
    
    prompt = (
        f"Based on this conversation context and recent web information, "
        f"provide a projection of what the research will likely find:\n\n"
        f"Conversation: {context_summary}\n\n"
        f"Recent web context: {web_context_summary}\n\n"
        f"Project what the academic research will likely reveal about this topic. "
        f"Be specific about expected findings, trends, and insights."
    )
    
    try:
        result = await llm_manager.model_dispatcher.dispatch_document({
            'id': 'projection-create',
            'title': 'Research Projection',
            'content': prompt
        }, is_critical=False)
        
        return result.get('raw_text', 'Based on the context, I expect to find relevant academic papers and insights.')
    except Exception:
        return "Based on the context gathered, I expect to find relevant academic papers and insights about this topic."

# This structure is extensible: you can add more nuanced logic, hybrid/parallel engines, and richer escalation as needed. 