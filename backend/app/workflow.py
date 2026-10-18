from __future__ import annotations

from typing import Annotated, Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from .config import get_settings
from .demo_scenarios import scenario_for
from .llm import vertex_json
from .youtube import search_youtube


class CurriculumState(TypedDict, total=False):
    topic: str
    timeframe_days: int
    current_skill_level: str
    user_id: str
    persona: dict
    lessons: list[dict]
    curated: list[dict]
    feedback_attempts: int
    needs_remap: bool
    result: dict


def learner_profiler(state: CurriculumState) -> dict:
    level = state["current_skill_level"]
    fallback = {"goal": state["topic"], "level": level, "pace": "focused daily sessions", "assumptions": ["Learner has access to YouTube", "Lessons should build progressively"]}
    persona = vertex_json(f"Return JSON for a learning persona. Goal: {state['topic']}. Level: {level}. Include goal, level, pace, and assumptions.", fallback)
    return {"persona": persona}


def curriculum_mapper(state: CurriculumState) -> dict:
    days = state["timeframe_days"]
    topic = state["topic"]
    prefix = "Foundations" if state["current_skill_level"] == "beginner" else "Applied practice"
    retry = state.get("feedback_attempts", 0)
    lesson_minutes = 12 if retry else 20
    scenario = scenario_for(topic, state["current_skill_level"]) if get_settings().local_demo_mode else None
    if scenario:
        lessons = [{"day": day, "title": item[0], "objective": item[1], "target_minutes": lesson_minutes} for day, item in enumerate(scenario["lessons"][:days], start=1)]
        if len(lessons) < days:
            lessons.extend({"day": day, "title": f"{prefix}: {topic} — applied practice {day}", "objective": f"Build one useful {topic} skill for day {day}.", "target_minutes": lesson_minutes} for day in range(len(lessons) + 1, days + 1))
        # Demo scenarios must remain deterministic and never be replaced by LLM output.
        return {"lessons": lessons, "needs_remap": False}
    else:
        lessons = [{"day": day, "title": f"{prefix}: {topic} — part {day}", "objective": f"Build one useful {topic} skill for day {day}.", "target_minutes": lesson_minutes} for day in range(1, days + 1)]
    generated = vertex_json(f"Return JSON object with a lessons array of exactly {days} progressive lessons for {topic}, aimed at a {state['current_skill_level']} learner. Each lesson needs day, title, objective, target_minutes <= {lesson_minutes}.", {"lessons": lessons})
    candidate = generated.get("lessons", lessons)
    if not isinstance(candidate, list) or len(candidate) != days or any(not isinstance(item, dict) or not {"day", "title", "objective", "target_minutes"}.issubset(item) for item in candidate):
        candidate = lessons
    lessons = candidate
    return {"lessons": lessons, "needs_remap": False}


def video_curator(state: CurriculumState) -> dict:
    # A curriculum performs one search, rather than one expensive search per day.
    # The returned library is matched across the lesson sequence.
    scenario = scenario_for(state["topic"], state["current_skill_level"]) if get_settings().local_demo_mode else None
    videos = scenario["videos"] if scenario else search_youtube(f"{state['topic']} {state['current_skill_level']} tutorial", state["user_id"])
    if not videos:
        return {"needs_remap": True, "feedback_attempts": state.get("feedback_attempts", 0) + 1}
    curated = [{**lesson, "video": videos[(int(lesson["day"]) - 1) % len(videos)]} for lesson in state["lessons"]]
    return {"curated": curated, "needs_remap": False}


def should_remap(state: CurriculumState) -> Literal["mapper", "planner"]:
    return "mapper" if state.get("needs_remap") and state.get("feedback_attempts", 0) <= 1 else "planner"


def lesson_planner(state: CurriculumState) -> dict:
    days = []
    for lesson in state.get("curated", []):
        days.append({**lesson, "why_chosen": f"This lesson directly supports the day {lesson['day']} objective and is selected to match a {state['current_skill_level']} learner."})
    return {"result": {"title": f"{state['topic']} in {state['timeframe_days']} days", "persona": state["persona"], "days": days, "gap_feedback_used": state.get("feedback_attempts", 0) > 0}}


def build_workflow():
    graph = StateGraph(CurriculumState)
    graph.add_node("profiler", learner_profiler)
    graph.add_node("mapper", curriculum_mapper)
    graph.add_node("curator", video_curator)
    graph.add_node("planner", lesson_planner)
    graph.add_edge(START, "profiler")
    graph.add_edge("profiler", "mapper")
    graph.add_edge("mapper", "curator")
    graph.add_conditional_edges("curator", should_remap, {"mapper": "mapper", "planner": "planner"})
    graph.add_edge("planner", END)
    return graph.compile()


workflow = build_workflow()
