from typing import Any, Dict, Optional, TypedDict
import os
from dotenv import load_dotenv
from langgraph.graph import START, StateGraph

from src.validator.runner import run_check
from src.validator.router import route_check

class State(TypedDict, total=False):
    check: str
    intent: Dict[str, Any]
    result: Dict[str, Any]


def _llm_route(text: str):
    load_dotenv(override=True)
    # Map Azure-style envs if present (plug actual OpenAI client later)
    if os.getenv("LLMFOUNDRY_TOKEN") and not os.getenv("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = os.getenv("LLMFOUNDRY_TOKEN")  # type: ignore
    if os.getenv("base_url") and not os.getenv("OPENAI_BASE_URL"):
        os.environ["OPENAI_BASE_URL"] = os.getenv("base_url")  # type: ignore
    if os.getenv("AZURE_API_VERSION") and not os.getenv("OPENAI_API_VERSION"):
        os.environ["OPENAI_API_VERSION"] = os.getenv("AZURE_API_VERSION")  # type: ignore
    return route_check(text)


def build_graph(stock_df, master_df, gr_df):
    def route_node(state: State):
        check = state.get("check")
        if not check and "input" in state:  # langgraph may inject 'input' key
            state["check"] = state["input"]  # type: ignore
            check = state["check"]
        intent = _llm_route(check)  # type: ignore
        state["intent"] = intent  # type: ignore
        return state

    def act_node(state: State):
        check = state["check"]
        result = run_check(check, stock_df=stock_df, master_df=master_df, gr_df=gr_df)
        state["result"] = result
        return state

    g = StateGraph(State)
    g.add_node("route", route_node)
    g.add_node("act", act_node)
    g.add_edge(START, "route")
    g.add_edge("route", "act")
    return g.compile()
