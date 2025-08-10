"""AI agents (pydantic-ai) used across the system.

We keep this module small so we can later expand with different prompt specializations.
"""
from __future__ import annotations

from typing import List

from app.config.settings import get_settings

try:  # pragma: no cover - optional import
	from pydantic_ai import Agent  # type: ignore
except Exception:  # pragma: no cover - library import guard
	Agent = None  # type: ignore

_explanation_agent = None


def _get_explanation_agent():
	"""Lazy init of explanation agent.

	NOTE: pydantic-ai model string may require provider prefix depending on version.
	Adjust `model=` here if failures occur (e.g., "openai:gpt-4o-mini").
	"""
	global _explanation_agent
	if _explanation_agent is None and Agent is not None:
		settings = get_settings()
		system = (
			"You are a senior technical writer. Given a documentation or code snippet, "
			"produce a concise 2-3 sentence explanation that captures intent, key behavior, "
			"and when to use it. Avoid fluff, no introductions like 'This snippet'."
		)
		try:
			_explanation_agent = Agent(model=settings.openai_chat_model, system_prompt=system)  # type: ignore[arg-type]
		except Exception:  # pragma: no cover
			_explanation_agent = None
	return _explanation_agent


async def generate_explanations(snippets: List[str]) -> List[str]:
	"""Generate explanations for each snippet; gracefully degrade on failures.

	If the agent or API key is missing we return blank strings of matching length so callers
	can still function.
	"""
	agent = _get_explanation_agent()
	if agent is None or not get_settings().openai_api_key:
		return ["" for _ in snippets]
	results: List[str] = []
	for s in snippets:
		try:
			# Depending on pydantic-ai version, run may be sync/async. We try async first.
			run_obj = agent.run(s)  # type: ignore
			if hasattr(run_obj, "__await__"):
				run_obj = await run_obj  # type: ignore
			# run_obj may have .content or be plain string
			if hasattr(run_obj, "content"):
				results.append(str(run_obj.content).strip())
			else:
				results.append(str(run_obj.output).strip())
		except Exception:
			results.append("")
	return results

__all__ = ["generate_explanations"]

