import pytest
from kernel.planning.planner import Planner
from kernel.planning.task_plan import TaskPlan
from kernel.planning.execution_step import ExecutionStep


def test_supports_goal():
    planner = Planner()
    assert planner.supports_goal("Research FastAPI") is True
    assert planner.supports_goal("   ") is False


def test_create_plan_returns_task_plan():
    planner = Planner()
    plan = planner.create_plan("Research FastAPI")
    assert isinstance(plan, TaskPlan)
    assert plan.goal == "Research FastAPI"
    assert plan.step_count() == 1
    assert isinstance(plan.plan_id, str)
    assert plan.plan_id.strip() != ""


def test_plan_contains_research_step():
    planner = Planner()
    plan = planner.create_plan("Research FastAPI")
    assert plan.step_count() == 1
    step = plan.steps[0]
    assert isinstance(step, ExecutionStep)
    assert step.step_id == "step-1"
    assert step.adapter == "research"
    assert step.intent == "research"
    assert step.payload == {"query": "Research FastAPI"}
    assert step.description == "Research the requested goal."
    assert step.optional is False


def test_plan_to_dict():
    planner = Planner()
    plan = planner.create_plan("Research FastAPI")
    plan_dict = plan.to_dict()
    assert isinstance(plan_dict, dict)
    assert "plan_id" in plan_dict
    assert "goal" in plan_dict
    assert "steps" in plan_dict
    assert "metadata" in plan_dict
    assert plan_dict["goal"] == "Research FastAPI"
    assert isinstance(plan_dict["steps"], list)
    assert len(plan_dict["steps"]) == 1
    step = plan_dict["steps"][0]
    assert step["adapter"] == "research"
    assert step["intent"] == "research"
    assert step["payload"] == {"query": "Research FastAPI"}