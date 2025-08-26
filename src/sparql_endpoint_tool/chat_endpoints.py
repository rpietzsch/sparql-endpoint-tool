"""Chat endpoints for AI-powered SPARQL assistance."""

from typing import List, Optional, Dict, Any
import logging
from fastapi import HTTPException
from pydantic import BaseModel

from .ai_services import get_ai_manager, ChatMessage, AIProvider
from .config import get_config

logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    """Request model for chat interactions."""
    message: str
    current_query: Optional[str] = None
    provider: Optional[AIProvider] = None
    conversation_history: Optional[List[Dict[str, str]]] = None


class ChatResponse(BaseModel):
    """Response model for chat interactions."""
    response: str
    suggested_query: Optional[str] = None
    provider_used: str


class QueryInterpretationRequest(BaseModel):
    """Request model for query interpretation."""
    query: str
    provider: Optional[AIProvider] = None


class QueryGenerationRequest(BaseModel):
    """Request model for query generation."""
    description: str
    current_query: Optional[str] = None
    provider: Optional[AIProvider] = None


def get_graph_context(graph) -> str:
    """Get context information about the current graph."""
    
    context_parts = [
        f"The RDF graph contains {len(graph)} triples."
    ]
    
    # Get sample triples for context
    sample_triples = []
    count = 0
    for s, p, o in graph:
        if count >= 10:  # Limit to 10 sample triples
            break
        sample_triples.append(f"  {s} {p} {o}")
        count += 1
    
    if sample_triples:
        context_parts.append("Sample triples:")
        context_parts.extend(sample_triples)
    
    # Get namespaces
    namespaces = list(graph.namespaces())
    if namespaces:
        context_parts.append("Available namespaces:")
        for prefix, namespace in namespaces[:10]:  # Limit to 10 namespaces
            if prefix:
                context_parts.append(f"  PREFIX {prefix}: <{namespace}>")
    
    return "\n".join(context_parts)


def create_system_message(graph, task_type: str = "general") -> ChatMessage:
    """Create system message with graph context."""
    
    graph_context = get_graph_context(graph)
    
    if task_type == "interpret":
        system_prompt = f"""You are an expert SPARQL assistant. Your task is to explain SPARQL queries in clear, natural language.

Graph Context:
{graph_context}

When explaining a query:
1. Describe what the query is trying to find/retrieve
2. Explain any filters, conditions, or patterns used
3. Mention the expected result format (SELECT, ASK, CONSTRUCT, etc.)
4. Keep explanations clear and accessible to users with varying SPARQL knowledge

Be concise but comprehensive in your explanations."""

    elif task_type == "generate":
        system_prompt = f"""You are an expert SPARQL assistant. Your task is to generate SPARQL queries based on natural language descriptions.

Graph Context:
{graph_context}

When generating queries:
1. Use appropriate prefixes from the available namespaces
2. Create efficient and correct SPARQL syntax
3. Include relevant LIMIT clauses when appropriate
4. Consider the actual structure and content of the graph
5. If modifying an existing query, preserve its structure when possible

Always return valid SPARQL that works with the provided graph structure."""

    else:  # general chat
        system_prompt = f"""You are an expert SPARQL assistant helping users work with RDF data and SPARQL queries.

Graph Context:
{graph_context}

You can help with:
1. Explaining SPARQL queries in natural language
2. Generating SPARQL queries from descriptions
3. Modifying and improving existing queries
4. Answering questions about SPARQL syntax and best practices
5. Providing guidance on working with RDF data

Always provide practical, accurate assistance focused on SPARQL and RDF concepts."""

    return ChatMessage("system", system_prompt)


async def interpret_query(graph, request: QueryInterpretationRequest) -> ChatResponse:
    """Interpret a SPARQL query and explain it in natural language."""
    
    try:
        ai_manager = get_ai_manager()
        if not ai_manager.is_enabled():
            raise HTTPException(status_code=503, detail="AI features are not configured")
        
        # Create conversation messages
        messages = [
            create_system_message(graph, "interpret"),
            ChatMessage("user", f"Please explain this SPARQL query:\n\n```sparql\n{request.query}\n```")
        ]
        
        # Generate response
        response = await ai_manager.generate_response(messages, request.provider)
        
        # Determine which provider was used
        provider_used = request.provider or ai_manager.config.ai.default_provider
        
        return ChatResponse(
            response=response,
            provider_used=provider_used.value
        )
        
    except Exception as e:
        logger.error(f"Query interpretation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def generate_query(graph, request: QueryGenerationRequest) -> ChatResponse:
    """Generate a SPARQL query from natural language description."""
    
    try:
        ai_manager = get_ai_manager()
        if not ai_manager.is_enabled():
            raise HTTPException(status_code=503, detail="AI features are not configured")
        
        # Create conversation messages
        messages = [create_system_message(graph, "generate")]
        
        # Add current query context if provided
        user_message = f"Generate a SPARQL query for: {request.description}"
        if request.current_query:
            user_message += f"\n\nCurrent query (modify if needed):\n```sparql\n{request.current_query}\n```"
        
        messages.append(ChatMessage("user", user_message))
        
        # Generate response
        response = await ai_manager.generate_response(messages, request.provider)
        
        # Try to extract SPARQL query from response
        suggested_query = extract_sparql_from_response(response)
        
        # Determine which provider was used
        provider_used = request.provider or ai_manager.config.ai.default_provider
        
        return ChatResponse(
            response=response,
            suggested_query=suggested_query,
            provider_used=provider_used.value
        )
        
    except Exception as e:
        logger.error(f"Query generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def chat_conversation(graph, request: ChatRequest) -> ChatResponse:
    """Handle general chat conversation with context."""
    
    try:
        ai_manager = get_ai_manager()
        if not ai_manager.is_enabled():
            raise HTTPException(status_code=503, detail="AI features are not configured")
        
        # Create conversation messages
        messages = [create_system_message(graph, "general")]
        
        # Add conversation history if provided
        if request.conversation_history:
            for msg in request.conversation_history:
                messages.append(ChatMessage(msg["role"], msg["content"]))
        
        # Add current query context if provided
        context_parts = []
        if request.current_query:
            context_parts.append(f"Current query:\n```sparql\n{request.current_query}\n```")
        
        context_parts.append(f"User message: {request.message}")
        
        messages.append(ChatMessage("user", "\n\n".join(context_parts)))
        
        # Generate response
        response = await ai_manager.generate_response(messages, request.provider)
        
        # Try to extract SPARQL query from response if it looks like query generation
        suggested_query = None
        if any(keyword in request.message.lower() for keyword in ['query', 'select', 'find', 'show', 'get', 'list']):
            suggested_query = extract_sparql_from_response(response)
        
        # Determine which provider was used
        provider_used = request.provider or ai_manager.config.ai.default_provider
        
        return ChatResponse(
            response=response,
            suggested_query=suggested_query,
            provider_used=provider_used.value
        )
        
    except Exception as e:
        logger.error(f"Chat conversation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def extract_sparql_from_response(response: str) -> Optional[str]:
    """Extract SPARQL query from AI response if present."""
    
    import re
    
    # Look for SPARQL code blocks
    sparql_patterns = [
        r'```sparql\n(.*?)\n```',
        r'```\n(.*?)\n```',
        r'SELECT.*?(?:\n\n|\Z)',
        r'ASK.*?(?:\n\n|\Z)',
        r'CONSTRUCT.*?(?:\n\n|\Z)',
        r'DESCRIBE.*?(?:\n\n|\Z)'
    ]
    
    for pattern in sparql_patterns:
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        if match:
            query = match.group(1).strip()
            # Basic validation - check if it looks like SPARQL
            if any(keyword in query.upper() for keyword in ['SELECT', 'WHERE', 'ASK', 'CONSTRUCT', 'DESCRIBE']):
                return query
    
    return None


def get_ai_status() -> Dict[str, Any]:
    """Get current AI configuration status."""
    
    config = get_config()
    
    if not config.ai.enabled:
        return {
            "enabled": False,
            "providers": [],
            "default_provider": None,
            "message": "AI features are disabled"
        }
    
    try:
        ai_manager = get_ai_manager()
        available_providers = ai_manager.get_available_providers()
        
        return {
            "enabled": True,
            "providers": [p.value for p in available_providers],
            "default_provider": config.ai.default_provider.value,
            "message": f"{len(available_providers)} AI provider(s) available"
        }
        
    except Exception as e:
        return {
            "enabled": False,
            "providers": [],
            "default_provider": None,
            "message": f"AI configuration error: {str(e)}"
        }