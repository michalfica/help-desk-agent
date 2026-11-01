"""Tool-calling loop shared by the live agent and offline tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from . import tools


CONTACT_MESSAGE = "Please contact CityWheels staff at help@citywheels.example or +48 000 000 000."
MAX_TOOL_ROUNDS = 8


@dataclass
class ModelResponse:
    text: str | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)


class ToolCallingModel(Protocol):
    def start(self, question: str) -> ModelResponse: ...

    def send_tool_results(self, results: list[dict[str, Any]]) -> ModelResponse: ...


TOOL_FUNCTIONS = {
    "search_policies": tools.search_policies,
    "get_booking": tools.get_booking,
    "calculate_refund": tools.calculate_refund,
}


class HelpDeskAgent:
    def __init__(self, model: ToolCallingModel, max_tool_rounds: int = MAX_TOOL_ROUNDS):
        self.model = model
        self.max_tool_rounds = max_tool_rounds
        self.last_tool_calls: list[dict[str, Any]] = []

    def answer(self, question: str) -> str:
        self.last_tool_calls = []
        response = self.model.start(question)
        if not response.tool_calls:
            return f"I cannot answer from the available CityWheels information. {CONTACT_MESSAGE}"

        for _ in range(self.max_tool_rounds):
            if not response.tool_calls:
                return response.text or f"I could not find a reliable answer. {CONTACT_MESSAGE}"

            results: list[dict[str, Any]] = []
            for call in response.tool_calls:
                name = str(call.get("name", ""))
                arguments = call.get("arguments", {})
                self.last_tool_calls.append({"name": name, "arguments": arguments})
                function = TOOL_FUNCTIONS.get(name)
                if function is None:
                    result = {"error": f"Unknown tool: {name}"}
                elif not isinstance(arguments, dict):
                    result = {"error": "Tool arguments must be an object."}
                else:
                    try:
                        result = function(**arguments)
                    except (TypeError, ValueError) as error:
                        result = {"error": str(error)}
                if isinstance(result, dict) and result.get("found") is False:
                    if name == "search_policies":
                        return f"I cannot answer from the available CityWheels information. {CONTACT_MESSAGE}"
                    if name in {"get_booking", "calculate_refund"}:
                        booking_id = result.get("booking_id", "that booking")
                        return f"Booking {booking_id} was not found. {CONTACT_MESSAGE}"
                results.append({"name": name, "response": result})

            response = self.model.send_tool_results(results)

        return f"I could not complete that request. {CONTACT_MESSAGE}"