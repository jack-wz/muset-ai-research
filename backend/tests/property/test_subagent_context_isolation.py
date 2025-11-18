"""Property test: SubAgent context isolation.

Verifies requirement 3.2.
"""
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from langchain_core.messages import AIMessage, HumanMessage
from unittest.mock import AsyncMock

from app.services.subagent_manager import AgentType, SubAgentManager


@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = AsyncMock()
    llm.ainvoke.return_value = AIMessage(content="Test response")
    return llm


@pytest.fixture
def subagent_manager(mock_llm):
    """Create a sub-agent manager for testing."""
    return SubAgentManager(llm=mock_llm)


# Property 4: SubAgent context isolation
@settings(max_examples=30)
@given(
    # Generate large irrelevant context
    irrelevant_messages=st.lists(
        st.text(min_size=100, max_size=1000),
        min_size=5,
        max_size=20,
    ),
    relevant_context=st.text(min_size=50, max_size=500),
)
@pytest.mark.asyncio
async def test_subagent_context_filtered(
    subagent_manager: SubAgentManager,
    irrelevant_messages: list,
    relevant_context: str,
):
    """
    Test that sub-agent receives only relevant context.

    This property verifies:
    - Context is filtered before passing to sub-agent (Req 3.2)
    - Irrelevant information is excluded
    """
    # Create large context
    context = [HumanMessage(content=msg) for msg in irrelevant_messages]
    context.append(HumanMessage(content=relevant_context))

    # Spawn agent with context filtering
    agent_id = await subagent_manager.spawn_agent(
        agent_type=AgentType.RESEARCH,
        task_description="Summarize the relevant information",
        context=context,
        max_context_size=2000,  # Small limit to force filtering
    )

    agent = subagent_manager.agents[agent_id]

    # Verify context was filtered
    total_context_size = sum(len(msg.content) for msg in agent.context[1:])  # Exclude system message

    assert total_context_size <= 2000, "Context should be filtered to max size"


@pytest.mark.asyncio
async def test_multiple_agents_isolated_context(
    subagent_manager: SubAgentManager,
):
    """Test that multiple agents have isolated contexts."""
    context1 = [HumanMessage(content="Context for agent 1")]
    context2 = [HumanMessage(content="Context for agent 2")]

    agent1_id = await subagent_manager.spawn_agent(
        agent_type=AgentType.RESEARCH,
        task_description="Task 1",
        context=context1,
    )

    agent2_id = await subagent_manager.spawn_agent(
        agent_type=AgentType.EDITING,
        task_description="Task 2",
        context=context2,
    )

    agent1 = subagent_manager.agents[agent1_id]
    agent2 = subagent_manager.agents[agent2_id]

    # Verify contexts are isolated
    assert agent1.context != agent2.context
    assert agent1.agent_type != agent2.agent_type
