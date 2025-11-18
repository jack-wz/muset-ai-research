"""Task planner for DeepAgent."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import TodoTask, WritingPlan


class TaskPlanner:
    """Plans and manages writing tasks using LLM analysis."""

    def __init__(self, session: AsyncSession, llm: BaseChatModel):
        """
        Initialize task planner.

        Args:
            session: Database session
            llm: Language model for task analysis
        """
        self.session = session
        self.llm = llm

    async def analyze_goal(self, goal: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a writing goal and break it down into tasks.

        Args:
            goal: Writing goal description
            context: Optional additional context

        Returns:
            Dictionary with analyzed goal and suggested tasks
        """
        system_prompt = """You are a writing task planner. Analyze the user's writing goal and break it down into concrete, actionable tasks.

For each task, identify:
1. A clear title and description
2. The task type (outline, draft, research, edit, publish)
3. Priority (low, medium, high)
4. Dependencies on other tasks (use task indices)

Your response should be in the following JSON format:
{
  "analysis": "Brief analysis of the goal",
  "tasks": [
    {
      "title": "Task title",
      "description": "Detailed description",
      "type": "outline|draft|research|edit|publish",
      "priority": "low|medium|high",
      "dependencies": []
    }
  ]
}

Ensure tasks form a DAG (Directed Acyclic Graph) - no circular dependencies."""

        user_prompt = f"Goal: {goal}"
        if context:
            user_prompt += f"\n\nContext: {context}"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        response = await self.llm.ainvoke(messages)

        # Parse response
        import json

        try:
            result = json.loads(response.content)
            return result
        except json.JSONDecodeError:
            # Fallback to basic task structure
            return {
                "analysis": "Could not parse structured response",
                "tasks": [
                    {
                        "title": "Complete the writing goal",
                        "description": goal,
                        "type": "draft",
                        "priority": "high",
                        "dependencies": [],
                    }
                ],
            }

    async def create_todos(
        self,
        workspace_id: str,
        goal: str,
        page_id: Optional[str] = None,
        context: Optional[str] = None,
    ) -> WritingPlan:
        """
        Create a writing plan with todo tasks.

        Args:
            workspace_id: Workspace ID
            goal: Writing goal
            page_id: Optional page ID
            context: Optional context

        Returns:
            Created WritingPlan instance
        """
        # Analyze goal
        analysis = await self.analyze_goal(goal, context)

        # Create writing plan
        plan = WritingPlan(
            workspace_id=workspace_id,
            page_id=page_id,
            goal=goal,
            source_prompt=goal if not context else f"{goal}\n\nContext: {context}",
            status="active",
        )

        self.session.add(plan)
        await self.session.flush()

        # Create tasks
        tasks = []
        for i, task_data in enumerate(analysis.get("tasks", [])):
            task = TodoTask(
                plan_id=plan.id,
                title=task_data.get("title", f"Task {i + 1}"),
                description=task_data.get("description", ""),
                status="pending",
                step_type=task_data.get("type", "draft"),
                priority=task_data.get("priority", "medium"),
                dependencies=task_data.get("dependencies", []),
                outputs=[],
            )
            tasks.append(task)
            self.session.add(task)

        await self.session.commit()
        await self.session.refresh(plan)

        return plan

    async def update_plan(
        self,
        plan_id: UUID,
        updates: Dict[str, Any],
    ) -> WritingPlan:
        """
        Update a writing plan.

        Args:
            plan_id: Plan ID
            updates: Dictionary of updates

        Returns:
            Updated WritingPlan instance

        Raises:
            ValueError: If plan not found
        """
        result = await self.session.execute(select(WritingPlan).where(WritingPlan.id == plan_id))
        plan = result.scalar_one_or_none()

        if not plan:
            raise ValueError(f"Plan {plan_id} not found")

        # Update fields
        for key, value in updates.items():
            if hasattr(plan, key):
                setattr(plan, key, value)

        plan.updated_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(plan)

        return plan

    async def get_next_task(self, plan_id: UUID) -> Optional[TodoTask]:
        """
        Get the next task to execute.

        Args:
            plan_id: Plan ID

        Returns:
            Next TodoTask or None if no tasks available
        """
        result = await self.session.execute(select(WritingPlan).where(WritingPlan.id == plan_id))
        plan = result.scalar_one_or_none()

        if not plan:
            return None

        # Get all tasks for this plan
        tasks_result = await self.session.execute(
            select(TodoTask).where(TodoTask.plan_id == plan_id)
        )
        tasks = tasks_result.scalars().all()

        # Find next available task
        for task in tasks:
            if task.status == "pending":
                # Check if dependencies are met
                if await self._are_dependencies_met(task, tasks):
                    return task

        return None

    async def validate_dependencies(self, plan_id: UUID) -> Dict[str, Any]:
        """
        Validate task dependencies form a DAG.

        Args:
            plan_id: Plan ID

        Returns:
            Dictionary with validation results
        """
        tasks_result = await self.session.execute(
            select(TodoTask).where(TodoTask.plan_id == plan_id)
        )
        tasks = list(tasks_result.scalars().all())

        # Build adjacency list
        task_map = {str(task.id): task for task in tasks}
        visited = set()
        rec_stack = set()

        def has_cycle(task_id: str) -> bool:
            """DFS to detect cycles."""
            visited.add(task_id)
            rec_stack.add(task_id)

            if task_id in task_map:
                task = task_map[task_id]
                for dep_id in task.dependencies:
                    if dep_id not in visited:
                        if has_cycle(dep_id):
                            return True
                    elif dep_id in rec_stack:
                        return True

            rec_stack.remove(task_id)
            return False

        # Check for cycles
        for task_id in task_map:
            if task_id not in visited:
                if has_cycle(task_id):
                    return {
                        "valid": False,
                        "error": "Circular dependencies detected",
                    }

        return {"valid": True}

    async def _are_dependencies_met(self, task: TodoTask, all_tasks: List[TodoTask]) -> bool:
        """Check if all task dependencies are completed."""
        if not task.dependencies:
            return True

        task_map = {str(t.id): t for t in all_tasks}

        for dep_id in task.dependencies:
            if dep_id in task_map:
                dep_task = task_map[dep_id]
                if dep_task.status != "completed":
                    return False

        return True
