"""
Agent tools package.

High-level tools for LangGraph agents interacting with the
MAS Memory Layer.
"""

from .ciar_tools import CIAR_TOOLS, ciar_calculate, ciar_explain, ciar_filter
from .synthesis_tools import SYNTHESIS_TOOLS, synthesize_knowledge
from .tier_tools import (
    TIER_TOOLS,
    l2_search_facts,
    l3_query_graph,
    l3_search_episodes,
    l4_search_knowledge,
)
from .unified_tools import UNIFIED_TOOLS, get_context_block, memory_query, memory_store

__all__ = [
    "CIAR_TOOLS",
    "SYNTHESIS_TOOLS",
    "TIER_TOOLS",
    "UNIFIED_TOOLS",
    # CIAR tools (Week 3)
    "ciar_calculate",
    "ciar_explain",
    "ciar_filter",
    "get_context_block",
    # Tier-specific tools (Week 3)
    "l2_search_facts",
    "l3_query_graph",
    "l3_search_episodes",
    "l4_search_knowledge",
    # Unified tools (Week 2)
    "memory_query",
    "memory_store",
    # Synthesis tools (Week 3)
    "synthesize_knowledge",
]

# All tools combined for easy registration
ALL_TOOLS = UNIFIED_TOOLS + CIAR_TOOLS + TIER_TOOLS + SYNTHESIS_TOOLS
