"""
DSRA V2 — Workflow Execution Engine
=====================================
Compiles and executes the research process steps as a Directed Acyclic Graph (DAG).
Handles parallelism, task outputs compilation, and execution state checks.
"""

from typing import Any, Callable, Coroutine
import asyncio

import structlog

from app.core.logging import get_logger

log = get_logger(__name__)


class WorkflowStep:
    """Represents a single step (node) in the research execution graph."""

    def __init__(
        self,
        name: str,
        func: Callable[..., Coroutine[Any, Any, Any]],
        depends_on: list[str] = None,
    ):
        self.name = name
        self.func = func
        self.depends_on = depends_on or []
        self.completed = False
        self.output: Any = None
        self.error: Exception | None = None


class WorkflowEngine:
    """
    Asynchronous DAG executor that determines execution order and runs steps.
    """

    def __init__(self) -> None:
        self.steps: dict[str, WorkflowStep] = {}

    def add_step(
        self,
        name: str,
        func: Callable[..., Coroutine[Any, Any, Any]],
        depends_on: list[str] = None,
    ) -> None:
        """Add a step to the execution DAG."""
        self.steps[name] = WorkflowStep(name, func, depends_on)

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the compiled DAG steps.
        Automatically runs independent steps in parallel.
        """
        pending_steps = set(self.steps.keys())
        running_tasks: dict[str, asyncio.Task] = {}

        while pending_steps or running_tasks:
            # 1. Find steps that have all their dependencies completed
            runnable_steps = []
            for step_name in list(pending_steps):
                step = self.steps[step_name]
                dependencies_met = all(
                    self.steps[dep].completed for dep in step.depends_on
                )
                if dependencies_met:
                    runnable_steps.append(step_name)

            # 2. Launch runnable steps in parallel
            for step_name in runnable_steps:
                pending_steps.remove(step_name)
                step = self.steps[step_name]
                # Trigger callback function with execution context and dependencies output
                task = asyncio.create_task(step.func(context))
                running_tasks[step_name] = task
                log.debug("workflow_step_started", step=step_name)

            if not running_tasks:
                if pending_steps:
                    # Circular dependency or deadlocks
                    raise RuntimeError("Deadlock detected in workflow DAG definition.")
                break

            # 3. Wait for at least one running task to finish
            done, _ = await asyncio.wait(
                running_tasks.values(), return_when=asyncio.FIRST_COMPLETED
            )

            # 4. Process completed tasks
            for task in done:
                # Find which step finished
                finished_step_name = None
                for name, t in running_tasks.items():
                    if t is task:
                        finished_step_name = name
                        break

                if finished_step_name:
                    del running_tasks[finished_step_name]
                    step = self.steps[finished_step_name]

                    try:
                        step.output = task.result()
                        step.completed = True
                        context[step.name] = step.output
                        log.debug("workflow_step_completed", step=finished_step_name)
                    except Exception as e:
                        step.error = e
                        log.error("workflow_step_failed", step=finished_step_name, error=str(e))
                        # Cancel all other running tasks on failure
                        for t in running_tasks.values():
                            t.cancel()
                        raise e

        return context
