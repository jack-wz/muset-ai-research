"""Unit tests for SubAgentManager."""
import pytest
from langchain_core.messages import AIMessage, HumanMessage
from unittest.mock import AsyncMock

from app.services.subagent_manager import AgentType, SubAgentManager


@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = AsyncMock()
    llm.ainvoke.return_value = AIMessage(content="Mocked response")
    return llm


@pytest.fixture
def subagent_manager(mock_llm):
    """Create a sub-agent manager for testing."""
    return SubAgentManager(llm=mock_llm)


@pytest.mark.asyncio
async def test_spawn_agent(subagent_manager: SubAgentManager):
    """Test spawning a new agent."""
    agent_id = await subagent_manager.spawn_agent(
        agent_type=AgentType.RESEARCH,
        task_description="Research AI trends",
    )

    assert agent_id is not None
    assert agent_id in subagent_manager.agents


@pytest.mark.asyncio
async def test_coordinate_agents(subagent_manager: SubAgentManager):
    """Test coordinating multiple agents."""
    # Spawn multiple agents
    agent1_id = await subagent_manager.spawn_agent(
        agent_type=AgentType.RESEARCH,
        task_description="Research topic A",
    )
    agent2_id = await subagent_manager.spawn_agent(
        agent_type=AgentType.EDITING,
        task_description="Edit document B",
    )

    # Coordinate execution
    results = await subagent_manager.coordinate_agents([agent1_id, agent2_id])

    assert len(results) == 2
    assert agent1_id in results
    assert agent2_id in results


@pytest.mark.asyncio
async def test_collect_results(subagent_manager: SubAgentManager):
    """Test collecting results from agents."""
    agent_id = await subagent_manager.spawn_agent(
        agent_type=AgentType.FACT_CHECK,
        task_description="Verify facts",
    )

    # Execute agent
    await subagent_manager.coordinate_agents([agent_id])

    # Collect results
    results = await subagent_manager.collect_results([agent_id])

    assert len(results) == 1
    assert results[0]["agent_id"] == agent_id


@pytest.mark.asyncio
async def test_agent_with_context(subagent_manager: SubAgentManager):
    """Test spawning agent with context."""
    context = [
        HumanMessage(content="Previous conversation context"),
    ]

    agent_id = await subagent_manager.spawn_agent(
        agent_type=AgentType.TRANSLATION,
        task_description="Translate to Spanish",
        context=context,
    )

    agent = subagent_manager.agents[agent_id]
    assert len(agent.context) > 1  # System prompt + context


@pytest.mark.asyncio
async def test_different_agent_types(subagent_manager: SubAgentManager):
    """Test creating different types of agents."""
    for agent_type in AgentType:
        agent_id = await subagent_manager.spawn_agent(
            agent_type=agent_type,
            task_description=f"Test {agent_type.value}",
        )

        agent = subagent_manager.agents[agent_id]
        assert agent.agent_type == agent_type
