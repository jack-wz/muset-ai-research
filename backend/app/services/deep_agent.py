"""DeepAgent implementation with LangGraph workflow."""
from typing import Annotated, Any, Dict, List, Optional, Sequence, TypedDict

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import BaseTool
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.file_system_manager import FileSystemManager
from app.services.memory_manager import MemoryManager
from app.services.subagent_manager import AgentType, SubAgentManager
from app.services.task_planner import TaskPlanner


# Define agent state
class AgentState(TypedDict):
    """State of the DeepAgent."""

    messages: Annotated[Sequence[BaseMessage], add_messages]
    workspace_id: str
    goal: Optional[str]
    plan_id: Optional[str]
    current_task: Optional[str]
    memories: List[Dict[str, Any]]
    files: List[str]
    next_action: Optional[str]


class DeepAgent:
    """DeepAgent orchestrator using LangGraph."""

    def __init__(
        self,
        workspace_id: str,
        session: AsyncSession,
        llm: BaseChatModel,
        embeddings: Embeddings,
        base_path: str,
        pinecone_api_key: Optional[str] = None,
        pinecone_index: Optional[str] = None,
    ):
        """
        Initialize DeepAgent.

        Args:
            workspace_id: Workspace identifier
            session: Database session
            llm: Language model
            embeddings: Embedding model
            base_path: Base path for file storage
            pinecone_api_key: Optional Pinecone API key
            pinecone_index: Optional Pinecone index name
        """
        self.workspace_id = workspace_id
        self.session = session
        self.llm = llm

        # Initialize managers
        self.file_manager = FileSystemManager(
            workspace_id=workspace_id,
            base_path=base_path,
            session=session,
        )

        self.task_planner = TaskPlanner(
            session=session,
            llm=llm,
        )

        self.memory_manager = MemoryManager(
            session=session,
            llm=llm,
            embeddings=embeddings,
            pinecone_api_key=pinecone_api_key,
            pinecone_index=pinecone_index,
        )

        self.subagent_manager = SubAgentManager(llm=llm)

        # Build graph
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        # Define workflow
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("analyze", self._analyze_goal)
        workflow.add_node("plan", self._create_plan)
        workflow.add_node("execute_task", self._execute_task)
        workflow.add_node("reflect", self._reflect_and_update)
        workflow.add_node("respond", self._generate_response)

        # Define edges
        workflow.set_entry_point("analyze")

        workflow.add_edge("analyze", "plan")
        workflow.add_edge("plan", "execute_task")
        workflow.add_edge("execute_task", "reflect")

        # Conditional edge from reflect
        workflow.add_conditional_edges(
            "reflect",
            self._should_continue,
            {
                "continue": "execute_task",
                "respond": "respond",
            },
        )

        workflow.add_edge("respond", END)

        return workflow.compile()

    async def _analyze_goal(self, state: AgentState) -> AgentState:
        """Analyze user goal and load relevant memories."""
        messages = state["messages"]
        last_message = messages[-1] if messages else None

        if not last_message:
            return state

        # Extract goal from message
        goal = last_message.content if isinstance(last_message, HumanMessage) else None

        if goal:
            state["goal"] = goal

            # Load relevant memories
            memories = await self.memory_manager.load_memories(
                workspace_id=self.workspace_id,
                query=goal,
                top_k=5,
            )

            state["memories"] = [
                {
                    "type": m.type,
                    "title": m.title,
                    "payload": m.payload,
                }
                for m in memories
            ]

        return state

    async def _create_plan(self, state: AgentState) -> AgentState:
        """Create a task plan."""
        goal = state.get("goal")

        if goal:
            # Create todos
            plan = await self.task_planner.create_todos(
                workspace_id=self.workspace_id,
                goal=goal,
            )

            state["plan_id"] = str(plan.id)

        return state

    async def _execute_task(self, state: AgentState) -> AgentState:
        """Execute the current task."""
        plan_id = state.get("plan_id")

        if not plan_id:
            return state

        # Get next task
        from uuid import UUID

        next_task = await self.task_planner.get_next_task(UUID(plan_id))

        if next_task:
            state["current_task"] = next_task.title

            # Execute task based on type
            if next_task.step_type == "research":
                # Spawn research agent
                agent_id = await self.subagent_manager.spawn_agent(
                    agent_type=AgentType.RESEARCH,
                    task_description=next_task.description,
                    context=state["messages"],
                )
                results = await self.subagent_manager.coordinate_agents([agent_id])
                result = results.get(agent_id, "")

                # Store result
                await self.file_manager.write_file(
                    f"research/{next_task.id}.md",
                    result,
                    category="draft",
                )

            elif next_task.step_type == "draft":
                # Generate draft
                messages = state["messages"] + [
                    SystemMessage(content=f"Task: {next_task.description}"),
                ]
                response = await self.llm.ainvoke(messages)

                # Write to file
                await self.file_manager.write_file(
                    f"drafts/{next_task.id}.md",
                    response.content,
                    category="draft",
                )

            # Mark task as completed
            next_task.status = "completed"
            await self.session.commit()

        return state

    async def _reflect_and_update(self, state: AgentState) -> AgentState:
        """Reflect on progress and update plan."""
        plan_id = state.get("plan_id")

        if plan_id:
            # Check if more tasks remain
            from uuid import UUID

            next_task = await self.task_planner.get_next_task(UUID(plan_id))

            if next_task:
                state["next_action"] = "continue"
            else:
                state["next_action"] = "respond"

        return state

    async def _generate_response(self, state: AgentState) -> AgentState:
        """Generate final response."""
        # Gather all outputs
        files = await self.file_manager.ls("drafts")
        state["files"] = files

        # Generate summary response
        messages = state["messages"] + [
            SystemMessage(
                content=f"Task completed. Generated files: {', '.join(files)}"
            ),
        ]
        response = await self.llm.ainvoke(messages)

        state["messages"] = state["messages"] + [response]

        return state

    def _should_continue(self, state: AgentState) -> str:
        """Determine if workflow should continue."""
        next_action = state.get("next_action", "respond")
        return next_action

    async def run(self, user_message: str) -> Dict[str, Any]:
        """
        Run the agent with a user message.

        Args:
            user_message: User input

        Returns:
            Agent response and state
        """
        # Initialize state
        initial_state: AgentState = {
            "messages": [HumanMessage(content=user_message)],
            "workspace_id": self.workspace_id,
            "goal": None,
            "plan_id": None,
            "current_task": None,
            "memories": [],
            "files": [],
            "next_action": None,
        }

        # Run workflow
        final_state = await self.workflow.ainvoke(initial_state)

        return {
            "response": final_state["messages"][-1].content,
            "files": final_state.get("files", []),
            "plan_id": final_state.get("plan_id"),
        }

    async def register_tool(self, tool: BaseTool) -> None:
        """
        Register a custom tool.

        Args:
            tool: LangChain tool to register
        """
        # Tools can be added to the workflow dynamically
        # This is a placeholder for tool registration
        pass
