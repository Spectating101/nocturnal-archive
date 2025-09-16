import re
import html
import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class InputValidator:
    """
    Comprehensive input validation and sanitization for security.
    """
    
    def __init__(self):
        # Define allowed patterns
        self.allowed_url_patterns = [
            r'^https?://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}(/\S*)?$',
            r'^https?://arxiv\.org/abs/\d+\.\d+$',
            r'^https?://doi\.org/10\.\d+/[a-zA-Z0-9\-\._/]+$',
            r'^https?://scholar\.google\.com/.*$',
            r'^https?://semanticscholar\.org/.*$',
            r'^https?://openalex\.org/.*$'
        ]
        
        # Define dangerous patterns
        self.dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'data:text/html',
            r'vbscript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>'
        ]
        
        # Compile patterns
        self.url_regex = re.compile('|'.join(self.allowed_url_patterns), re.IGNORECASE)
        self.dangerous_regex = re.compile('|'.join(self.dangerous_patterns), re.IGNORECASE)
    
    def validate_research_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize research request data."""
        try:
            validated = {}
            
            # Validate topic
            if 'topic' in data:
                validated['topic'] = self.sanitize_text(data['topic'], max_length=500)
                if not validated['topic']:
                    raise ValueError("Topic cannot be empty")
            
            # Validate research questions
            if 'research_questions' in data:
                questions = data['research_questions']
                if not isinstance(questions, list):
                    raise ValueError("Research questions must be a list")
                
                validated['research_questions'] = []
                for i, question in enumerate(questions[:10]):  # Limit to 10 questions
                    sanitized = self.sanitize_text(question, max_length=1000)
                    if sanitized:
                        validated['research_questions'].append(sanitized)
                
                if not validated['research_questions']:
                    raise ValueError("At least one valid research question is required")
            
            # Validate user_id
            if 'user_id' in data:
                validated['user_id'] = self.sanitize_text(data['user_id'], max_length=100)
                if not validated['user_id']:
                    raise ValueError("User ID cannot be empty")
            
            # Validate session_id (if provided)
            if 'session_id' in data:
                validated['session_id'] = self.sanitize_text(data['session_id'], max_length=100)
            
            return validated
            
        except Exception as e:
            logger.error(f"Research request validation failed: {e}")
            raise ValueError(f"Invalid research request: {str(e)}")
    
    def validate_chat_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize chat request data."""
        try:
            validated = {}
            
            # Validate messages
            if 'messages' not in data or not isinstance(data['messages'], list):
                raise ValueError("Messages must be a list")
            
            validated['messages'] = []
            for i, message in enumerate(data['messages'][:50]):  # Limit to 50 messages
                if not isinstance(message, dict):
                    continue
                
                sanitized_message = {
                    'role': self.sanitize_text(message.get('role', ''), max_length=20),
                    'content': self.sanitize_text(message.get('content', ''), max_length=10000)
                }
                
                if sanitized_message['role'] and sanitized_message['content']:
                    validated['messages'].append(sanitized_message)
            
            if not validated['messages']:
                raise ValueError("At least one valid message is required")
            
            # Validate optional fields
            if 'user_id' in data:
                validated['user_id'] = self.sanitize_text(data['user_id'], max_length=100)
            
            if 'workspace_id' in data:
                validated['workspace_id'] = self.sanitize_text(data['workspace_id'], max_length=100)
            
            if 'chatSettings' in data:
                validated['chatSettings'] = self.validate_chat_settings(data['chatSettings'])
            
            return validated
            
        except Exception as e:
            logger.error(f"Chat request validation failed: {e}")
            raise ValueError(f"Invalid chat request: {str(e)}")
    
    def validate_chat_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Validate chat settings."""
        validated = {}
        
        # Validate model
        if 'model' in settings:
            validated['model'] = self.sanitize_text(settings['model'], max_length=100)
        
        # Validate temperature
        if 'temperature' in settings:
            try:
                temp = float(settings['temperature'])
                validated['temperature'] = max(0.0, min(2.0, temp))  # Clamp between 0 and 2
            except (ValueError, TypeError):
                validated['temperature'] = 0.7  # Default
        
        # Validate max_tokens
        if 'max_tokens' in settings:
            try:
                tokens = int(settings['max_tokens'])
                validated['max_tokens'] = max(1, min(4000, tokens))  # Clamp between 1 and 4000
            except (ValueError, TypeError):
                validated['max_tokens'] = 1000  # Default
        
        return validated
    
    def validate_paper_upload(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate paper upload data."""
        try:
            validated = {}
            
            # Validate filename
            if 'filename' in data:
                validated['filename'] = self.sanitize_filename(data['filename'])
                if not validated['filename']:
                    raise ValueError("Invalid filename")
            
            # Validate content type
            if 'content_type' in data:
                content_type = data['content_type'].lower()
                allowed_types = ['text/plain', 'application/pdf', 'text/markdown']
                if content_type not in allowed_types:
                    raise ValueError(f"Unsupported content type: {content_type}")
                validated['content_type'] = content_type
            
            # Validate size (if provided)
            if 'size' in data:
                try:
                    size = int(data['size'])
                    if size > 50 * 1024 * 1024:  # 50MB limit
                        raise ValueError("File size too large")
                    validated['size'] = size
                except (ValueError, TypeError):
                    raise ValueError("Invalid file size")
            
            return validated
            
        except Exception as e:
            logger.error(f"Paper upload validation failed: {e}")
            raise ValueError(f"Invalid paper upload: {str(e)}")
    
    def validate_url(self, url: str) -> bool:
        """Validate if URL is safe and allowed."""
        if not url or not isinstance(url, str):
            return False
        
        # Check for dangerous patterns
        if self.dangerous_regex.search(url):
            logger.warning(f"Dangerous URL pattern detected: {url}")
            return False
        
        # Check if URL matches allowed patterns
        return bool(self.url_regex.match(url))
    
    def sanitize_text(self, text: str, max_length: int = 10000) -> str:
        """Sanitize text input."""
        if not text or not isinstance(text, str):
            return ""
        
        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length]
        
        # HTML escape
        text = html.escape(text)
        
        # Remove null bytes and control characters (except newlines and tabs)
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        
        # Remove dangerous patterns
        text = self.dangerous_regex.sub('', text)
        
        return text.strip()
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename."""
        if not filename or not isinstance(filename, str):
            return ""
        
        # Remove path traversal attempts
        filename = filename.replace('..', '').replace('/', '').replace('\\', '')
        
        # Remove dangerous characters
        filename = re.sub(r'[<>:"|?*]', '', filename)
        
        # Limit length
        if len(filename) > 255:
            filename = filename[:255]
        
        return filename.strip()
    
    def validate_json_payload(self, payload: str) -> Dict[str, Any]:
        """Validate and parse JSON payload."""
        try:
            if not payload or not isinstance(payload, str):
                raise ValueError("Payload must be a non-empty string")
            
            # Limit payload size
            if len(payload) > 1024 * 1024:  # 1MB limit
                raise ValueError("Payload too large")
            
            data = json.loads(payload)
            
            if not isinstance(data, dict):
                raise ValueError("Payload must be a JSON object")
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            raise ValueError("Invalid JSON payload")
        except Exception as e:
            logger.error(f"Payload validation failed: {e}")
            raise ValueError(f"Invalid payload: {str(e)}")
    
    def validate_search_query(self, query: str) -> str:
        """Validate search query."""
        if not query or not isinstance(query, str):
            raise ValueError("Search query cannot be empty")
        
        sanitized = self.sanitize_text(query, max_length=1000)
        if not sanitized:
            raise ValueError("Search query cannot be empty after sanitization")
        
        return sanitized
    
    def validate_session_id(self, session_id: str) -> str:
        """Validate session ID."""
        if not session_id or not isinstance(session_id, str):
            raise ValueError("Session ID cannot be empty")
        
        # Session ID should be alphanumeric with possible hyphens/underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', session_id):
            raise ValueError("Invalid session ID format")
        
        if len(session_id) > 100:
            raise ValueError("Session ID too long")
        
        return session_id
    
    def validate_user_id(self, user_id: str) -> str:
        """Validate user ID."""
        if not user_id or not isinstance(user_id, str):
            raise ValueError("User ID cannot be empty")
        
        # User ID should be alphanumeric with possible hyphens/underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', user_id):
            raise ValueError("Invalid user ID format")
        
        if len(user_id) > 100:
            raise ValueError("User ID too long")
        
        return user_id
    
    def validate_api_key(self, api_key: str) -> str:
        """Validate API key format."""
        if not api_key or not isinstance(api_key, str):
            raise ValueError("API key cannot be empty")
        
        # Basic API key validation (adjust based on your providers)
        if len(api_key) < 10 or len(api_key) > 200:
            raise ValueError("Invalid API key length")
        
        # Remove any whitespace
        api_key = api_key.strip()
        
        return api_key
    
    def create_validation_error_response(self, error: str) -> Dict[str, Any]:
        """Create a standardized validation error response."""
        return {
            "error": "validation_error",
            "message": error,
            "timestamp": datetime.utcnow().isoformat(),
            "status_code": 400
        }
