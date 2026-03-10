"""
====================================================================
  AGENTS — Constructs prompts and invokes the LLM for each
  research agent and the CIO synthesis.
====================================================================
"""

from datetime import datetime

from config import AGENTS, CIO_TASK, GROUNDING_INSTRUCTION, CONTENT_GUIDELINES, OPENROUTER_MODEL
from llm_client import call_openrouter
from market_data import format_snapshot_for_prompt, format_technical_block


def run_agent(api_key: str, agent_key: str, ticker: str,
              overview_data: dict | None = None,
              technical_data: dict | None = None,
              model: str = OPENROUTER_MODEL) -> str:
    """Run a single specialized research agent and return its report as a string."""
    agent = AGENTS[agent_key]
    print(f"  Generating analysis...")

    today = datetime.now().strftime("%B %d, %Y")
    task_content = agent["task"].format(ticker=ticker)
    system_content = f"{agent['persona']}\n\n{GROUNDING_INSTRUCTION}"
    snapshot_block = format_snapshot_for_prompt(overview_data) if overview_data else ""

    tech_block = ""
    if agent_key == "technical" and technical_data:
        tech_block = format_technical_block(technical_data, ticker=ticker)

    user_content = (
        f"Today's date is {today}.\n\n"
        + (f"{snapshot_block}\n\n" if snapshot_block else "")
        + (f"{tech_block}\n\n" if tech_block else "")
        + f"{task_content}\n\n"
        + f"{CONTENT_GUIDELINES}"
    )

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user",   "content": user_content},
    ]

    return call_openrouter(
        api_key, messages, temperature=0.3, max_tokens=1200, use_web_search=True, model=model
    )


def run_cio(api_key: str, ticker: str, agent_reports: dict, overview_data: dict | None = None,
            model: str = OPENROUTER_MODEL) -> str:
    """Synthesize all five agent reports into a final CIO verdict."""
    print("  Synthesizing all five reports...")

    snapshot_block = format_snapshot_for_prompt(overview_data) if overview_data else ""
    prompt = CIO_TASK.format(
        ticker=ticker,
        macro=agent_reports.get("macro", "[Agent did not run]"),
        flow=agent_reports.get("flow", "[Agent did not run]"),
        technical=agent_reports.get("technical", "[Agent did not run]"),
        narrative=agent_reports.get("narrative", "[Agent did not run]"),
        fundamental=agent_reports.get("fundamental", "[Agent did not run]"),
        market_snapshot=snapshot_block,
    )

    cio_system = (
        "You are the CIO of an elite multi-strategy hedge fund. "
        "Respond ONLY with the structured sections requested. "
        "Use bullet points (•) for all list items. "
        "Do NOT use markdown formatting. "
        "Do NOT add a SOURCES block."
    )
    messages = [
        {"role": "system", "content": cio_system},
        {"role": "user",   "content": prompt},
    ]
    return call_openrouter(api_key, messages, temperature=0.2, max_tokens=4500, model=model)
