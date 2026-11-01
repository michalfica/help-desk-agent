from __future__ import annotations

import unittest
from typing import Any

from citywheels.agent import HelpDeskAgent, ModelResponse


class FakeModel:
    def __init__(self, responses: list[ModelResponse]):
        self.responses = iter(responses)
        self.received_results: list[dict[str, Any]] = []

    def start(self, question: str) -> ModelResponse:
        self.question = question
        return next(self.responses)

    def send_tool_results(self, results: list[dict[str, Any]]) -> ModelResponse:
        self.received_results.extend(results)
        return next(self.responses)


class AgentLoopTests(unittest.TestCase):
    def test_executes_refund_tool_and_returns_model_final_answer(self) -> None:
        model = FakeModel([
            ModelResponse(tool_calls=[{
                "name": "calculate_refund",
                "arguments": {"booking_id": "CW-1002"},
            }]),
            ModelResponse(text="Your total refund is €340.00."),
        ])
        agent = HelpDeskAgent(model)

        answer = agent.answer("How much will I get for CW-1002?")

        self.assertIn("€340.00", answer)
        self.assertEqual("calculate_refund", model.received_results[0]["name"])
        self.assertEqual(340.0, model.received_results[0]["response"]["total_refund_eur"])
        self.assertEqual("calculate_refund", agent.last_tool_calls[0]["name"])

    def test_unknown_tool_does_not_crash_agent_loop(self) -> None:
        model = FakeModel([
            ModelResponse(tool_calls=[{"name": "missing_tool", "arguments": {}}]),
            ModelResponse(text="I cannot find that information. Contact staff."),
        ])
        answer = HelpDeskAgent(model).answer("Can you help?")
        self.assertIn("Contact staff", answer)
        self.assertEqual({"error": "Unknown tool: missing_tool"}, model.received_results[0]["response"])

    def test_refuses_model_only_answer_without_a_tool_result(self) -> None:
        model = FakeModel([ModelResponse(text="The capital is Canberra.")])
        answer = HelpDeskAgent(model).answer("What is the capital of Australia?")
        self.assertIn("cannot answer", answer.lower())
        self.assertIn("help@citywheels.example", answer)

    def test_unknown_booking_is_referred_without_trusting_model(self) -> None:
        model = FakeModel([
            ModelResponse(tool_calls=[{
                "name": "get_booking",
                "arguments": {"booking_id": "CW-9999"},
            }]),
        ])
        answer = HelpDeskAgent(model).answer("Check CW-9999")
        self.assertIn("not found", answer.lower())
        self.assertIn("help@citywheels.example", answer)
        self.assertEqual([], model.received_results)


if __name__ == "__main__":
    unittest.main()