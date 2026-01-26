"""
LLM service using Groq API for chat completions.
"""
import asyncio
from typing import AsyncGenerator, List, Dict, Any, Optional
import httpx
from groq import Groq, AsyncGroq
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMService:
    """Service for interacting with Groq LLM API."""
    
    def __init__(self):
        """Initialize Groq client."""
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL
        self.fallback_model = settings.GROQ_FALLBACK_MODEL
    
    def _build_system_prompt(
        self,
        company_name: str,
        context: str,
        chat_history: List[Dict[str, str]],
        tenant_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build the system prompt for the LLM.
        
        Args:
            company_name: Company/tenant name
            context: Retrieved context from RAG
            chat_history: Recent conversation history
            tenant_context: Optional context for customization
        
        Returns:
            str: System prompt
        """
        history_text = ""
        if chat_history:
            history_text = "\n".join([
                f"{msg['role'].upper()}: {msg['content']}"
                for msg in chat_history[-settings.CONVERSATION_HISTORY_LENGTH:]
            ])
            
        # Customize prompt based on tenant context
        tone = "professional, empathetic, and helpful"
        response_style = "concise"
        custom_instructions = ""
        
        if tenant_context:
            tone = tenant_context.get('tone_of_voice', tone)
            # Add other customizations as needed
            if tenant_context.get('custom_instructions'):
                custom_instructions = f"\nAdditional Instructions:\n{tenant_context['custom_instructions']}"
        
        prompt = f"""You are an expert customer support agent for {company_name}.
Your goal is to provide accurate, helpful answers based STRICTLY on the provided context.

Context from Knowledge Base:
{{context}}

Recent Conversation History:
{{history_text if history_text else 'None'}}

Instructions:
1. Carefully analyze the user's question and the provided context.
2. Think step-by-step: Does the context contain the answer? Is it complete or partial?
3. If the answer is explicitly in the context, provide it clearly and concisely.
4. If the context contains partial information, state what you know and what is missing.
5. If the answer is NOT in the context, respond: "I apologize, but I don't have that specific information in my knowledge base. Please contact our support team for assistance."
6. NEVER make up information or provide answers not supported by the context.
7. Format your response using Markdown (use bullet points, bold text) for readability.
8. Maintain a {tone} tone.
9. If the context contains conflicting information, acknowledge it and present both views.{custom_instructions}"""
        
        # Replace placeholders manually to avoid f-string complexity with braces
        prompt = prompt.replace("{context}", context)
        prompt = prompt.replace("{history_text if history_text else 'None'}", history_text if history_text else 'None')
        
        return prompt
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_response(
        self,
        user_message: str,
        context: str,
        company_name: str,
        chat_history: List[Dict[str, str]] = None,
        tenant_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a response using Groq LLM.
        
        Args:
            user_message: User's question
            context: Retrieved context from RAG
            company_name: Company/tenant name
            chat_history: Recent conversation history
            tenant_context: Optional context for customization
        
        Returns:
            str: LLM response
        """
        if chat_history is None:
            chat_history = []
        
        system_prompt = self._build_system_prompt(company_name, context, chat_history, tenant_context)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        try:
            logger.info(f"Generating response with {self.model}")
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=settings.GROQ_MAX_TOKENS,
                temperature=settings.GROQ_TEMPERATURE,
                stream=False
            )
            
            answer = response.choices[0].message.content
            logger.info(f"Generated response: {len(answer)} characters")
            
            return answer
            
        except Exception as e:
            logger.error(f"Error generating response with {self.model}: {e}")
            # Try fallback model
            try:
                logger.info(f"Retrying with fallback model {self.fallback_model}")
                response = await self.client.chat.completions.create(
                    model=self.fallback_model,
                    messages=messages,
                    max_tokens=settings.GROQ_MAX_TOKENS,
                    temperature=settings.GROQ_TEMPERATURE,
                    stream=False
                )
                return response.choices[0].message.content
            except Exception as fallback_error:
                logger.error(f"Fallback model also failed: {fallback_error}")
                raise
    
    async def generate_response_stream(
        self,
        user_message: str,
        context: str,
        company_name: str,
        chat_history: List[Dict[str, str]] = None,
        tenant_context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response using Groq LLM.
        
        Args:
            user_message: User's question
            context: Retrieved context from RAG
            company_name: Company/tenant name
            chat_history: Recent conversation history
        
        Yields:
            str: Response chunks
        """
        if chat_history is None:
            chat_history = []
        
        system_prompt = self._build_system_prompt(company_name, context, chat_history, tenant_context)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        try:
            logger.info(f"Generating streaming response with {self.model}")
            
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=settings.GROQ_MAX_TOKENS,
                temperature=settings.GROQ_TEMPERATURE,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            
        except Exception as e:
            logger.error(f"Error generating streaming response: {e}")
            yield f"Error: {str(e)}"
    
    def build_fallback_response(self, user_message: str) -> str:
        """
        Build a fallback response when no relevant context is found.
        
        Args:
            user_message: User's question
        
        Returns:
            str: Fallback response
        """
        return (
            "I apologize, but I don't have enough information in my knowledge base "
            "to answer your question accurately. Please contact our support team "
            "for further assistance, or try rephrasing your question."
        )
    
    async def health_check(self) -> bool:
        """
        Check if Groq API is accessible.
        
        Returns:
            bool: True if healthy
        """
        try:
            # Simple API call to check connectivity
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return True
        except Exception as e:
            logger.error(f"Groq API health check failed: {e}")
            return False


# Global LLM service instance
_llm_service: LLMService = None


def get_llm_service() -> LLMService:
    """
    Get the global LLM service instance.
    
    Returns:
        LLMService: LLM service
    """
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
