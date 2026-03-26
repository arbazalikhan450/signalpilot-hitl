from __future__ import annotations

from datetime import datetime
from typing import TypedDict

from langgraph.graph import END, StateGraph

from app.domain.enums import PostStatus


class PostWorkflowState(TypedDict, total=False):
    status: str
    scheduled_for: datetime | None


def mark_pending_approval(state: PostWorkflowState) -> PostWorkflowState:
    return {"status": PostStatus.PENDING_APPROVAL.value, "scheduled_for": state.get("scheduled_for")}


def route_after_approval(state: PostWorkflowState) -> str:
    if state["status"] == PostStatus.APPROVED.value and state.get("scheduled_for"):
        return "schedule_post"
    if state["status"] == PostStatus.APPROVED.value:
        return "approved_post"
    if state["status"] == PostStatus.REJECTED.value:
        return "rejected_post"
    return END


def schedule_post(state: PostWorkflowState) -> PostWorkflowState:
    return {"status": PostStatus.SCHEDULED.value, "scheduled_for": state.get("scheduled_for")}


def approved_post(state: PostWorkflowState) -> PostWorkflowState:
    return {"status": PostStatus.APPROVED.value, "scheduled_for": state.get("scheduled_for")}


def rejected_post(state: PostWorkflowState) -> PostWorkflowState:
    return {"status": PostStatus.REJECTED.value, "scheduled_for": state.get("scheduled_for")}


def build_post_workflow():
    graph = StateGraph(PostWorkflowState)
    graph.add_node("mark_pending_approval", mark_pending_approval)
    graph.set_entry_point("mark_pending_approval")
    graph.add_edge("mark_pending_approval", END)
    return graph.compile()


def apply_review_transition(status: PostStatus, scheduled_for: datetime | None):
    graph = StateGraph(PostWorkflowState)
    graph.add_node("router", lambda state: state)
    graph.add_node("schedule_post", schedule_post)
    graph.add_node("approved_post", approved_post)
    graph.add_node("rejected_post", rejected_post)
    graph.set_entry_point("router")
    graph.add_conditional_edges("router", route_after_approval)
    graph.add_edge("schedule_post", END)
    graph.add_edge("approved_post", END)
    graph.add_edge("rejected_post", END)
    workflow = graph.compile()
    return workflow.invoke({"status": status.value, "scheduled_for": scheduled_for})
