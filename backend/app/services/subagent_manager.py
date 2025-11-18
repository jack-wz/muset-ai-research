"""SubAgent manager for DeepAgent."""
import asyncio
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage


class AgentType(str, Enum):
    """Types of sub-agents."""

    RESEARCH = "research"
    TRANSLATION = "translation"
    EDITING = "editing"
    FACT_CHECK = "fact_check"


class SubAgent:
    """Represents a sub-agent with isolated context."""

    def __init__(
        self,
        agent_id: str,
        agent_type: AgentType,
        llm: BaseChatModel,
        context: List[BaseMessage],
        task_description: str,
    ):
        """
        Initialize sub-agent.

        Args:
            agent_id: Agent identifier
            agent_type: Type of agent
            llm: Language model
            context: Isolated context messages
            task_description: Task description
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.llm = llm
        self.context = context
        self.task_description = task_description
        self.result: Optional[str] = None

    async def execute(self) -> str:
        """
        Execute the agent's task.

        Returns:
            Task result
        """
        # Add task as user message
        messages = self.context + [HumanMessage(content=self.task_description)]

        # Invoke LLM
        response = await self.llm.ainvoke(messages)

        self.result = response.content
        return self.result


class SubAgentManager:
    """Manages sub-agents for parallel task execution."""

    def __init__(self, llm: BaseChatModel):
        """
        Initialize sub-agent manager.

        Args:
            llm: Language model for agents
        """
        self.llm = llm
        self.agents: Dict[str, SubAgent] = {}

    async def spawn_agent(
        self,
        agent_type: AgentType,
        task_description: str,
        context: Optional[List[BaseMessage]] = None,
        max_context_size: int = 5000,
    ) -> str:
        """
        Spawn a new sub-agent.

        Args:
            agent_type: Type of agent to spawn
            task_description: Task description
            context: Optional context messages
            max_context_size: Maximum context size in characters

        Returns:
            Agent ID
        """
        agent_id = str(uuid4())

        # Get system prompt for agent type
        system_prompt = self._get_system_prompt(agent_type)

        # Filter and prepare context
        filtered_context = await self._filter_context(
            context or [], task_description, max_context_size
        )

        # Create agent
        agent = SubAgent(
            agent_id=agent_id,
            agent_type=agent_type,
            llm=self.llm,
            context=[SystemMessage(content=system_prompt)] + filtered_context,
            task_description=task_description,
        )

        self.agents[agent_id] = agent

        return agent_id

    async def coordinate_agents(
        self,
        agent_ids: List[str],
    ) -> Dict[str, str]:
        """
        Execute multiple agents in parallel.

        Args:
            agent_ids: List of agent IDs to execute

        Returns:
            Dictionary mapping agent IDs to results
        """
        # Create tasks
        tasks = []
        for agent_id in agent_ids:
            if agent_id in self.agents:
                tasks.append(self.agents[agent_id].execute())

        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect results
        output = {}
        for agent_id, result in zip(agent_ids, results):
            if isinstance(result, Exception):
                output[agent_id] = f"Error: {str(result)}"
            else:
                output[agent_id] = result

        return output

    async def collect_results(self, agent_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Collect results from agents.

        Args:
            agent_ids: List of agent IDs

        Returns:
            List of result dictionaries
        """
        results = []
        for agent_id in agent_ids:
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                results.append(
                    {
                        "agent_id": agent_id,
                        "agent_type": agent.agent_type.value,
                        "task": agent.task_description,
                        "result": agent.result,
                    }
                )

        return results

    def _get_system_prompt(self, agent_type: AgentType) -> str:
        """Get system prompt for agent type."""
        prompts = {
            AgentType.RESEARCH: """You are a research assistant. Your task is to find and summarize relevant information on the given topic. Provide accurate, well-sourced information.""",
            AgentType.TRANSLATION: """You are a translation specialist. Your task is to translate the provided text while preserving tone, style, and meaning. Ensure cultural appropriateness.""",
            AgentType.EDITING: """You are an editing assistant. Your task is to improve the provided text by fixing grammar, enhancing clarity, and maintaining consistency. Preserve the author's voice.""",
            AgentType.FACT_CHECK: """You are a fact-checking assistant. Your task is to verify claims and identify potential inaccuracies in the provided text. Provide evidence for your findings.""",
        }
        return prompts.get(agent_type, "You are a helpful assistant.")

    async def _filter_context(
        self,
        context: List[BaseMessage],
        task_description: str,
        max_size: int,
    ) -> List[BaseMessage]:
        """
        Filter context to include only relevant information.

        Args:
            context: Original context messages
            task_description: Task description
            max_size: Maximum context size in characters

        Returns:
            Filtered context messages
        """
        if not context:
            return []

        # Calculate total size
        total_size = sum(len(msg.content) for msg in context)

        # If under limit, return all
        if total_size <= max_size:
            return context

        # Use LLM to select relevant context
        system_prompt = f"""You are a context filtering assistant. Given a list of messages and a task description, select the most relevant messages that will help complete the task.

Task: {task_description}

Return the indices of relevant messages (0-indexed) as a JSON array. Example: [0, 2, 5]"""

        # Create context summary
        context_summary = "\n\n".join(
            [f"[{i}] {msg.content[:200]}..." for i, msg in enumerate(context)]
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Messages:\n\n{context_summary}"),
        ]

        response = await self.llm.ainvoke(messages)

        # Parse response
        import json

        try:
            indices = json.loads(response.content)
            filtered = [context[i] for i in indices if i < len(context)]

            # Ensure we're under the limit
            filtered_size = sum(len(msg.content) for msg in filtered)
            if filtered_size > max_size:
                # Truncate messages
                result = []
                current_size = 0
                for msg in filtered:
                    if current_size + len(msg.content) <= max_size:
                        result.append(msg)
                        current_size += len(msg.content)
                    else:
                        break
                return result

            return filtered
        except (json.JSONDecodeError, IndexError):
            # Fallback: take most recent messages
            result = []
            current_size = 0
            for msg in reversed(context):
                if current_size + len(msg.content) <= max_size:
                    result.insert(0, msg)
                    current_size += len(msg.content)
                else:
                    break
            return result
