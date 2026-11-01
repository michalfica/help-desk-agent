from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from citywheels.agent import HelpDeskAgent, ModelResponse
from citywheels.config import load_environment
from citywheels.gemini import GeminiModel


class ScenarioModel:
    """Offline harness model: replays expected tool calls, then formats tool data."""

    def __init__(self, scenario: dict[str, Any]):
        self.scenario = scenario

    def start(self, question: str) -> ModelResponse:
        calls = self.scenario["offline_tool_calls"]
        if calls:
            return ModelResponse(tool_calls=calls)
        return ModelResponse(text=self.scenario.get("offline_answer", ""))

    def send_tool_results(self, results: list[dict[str, Any]]) -> ModelResponse:
        for item in results:
            result = item["response"]
            if item["name"] == "search_policies":
                if not result.get("found"):
                    return ModelResponse(text=refusal_answer())
                excerpts = [
                    f"[{match['section']}] {match['text']}"
                    for match in result["matches"]
                ]
                return ModelResponse(text="CityWheels policy: " + "\n".join(excerpts))
            if item["name"] == "get_booking":
                if not result.get("found"):
                    return ModelResponse(text=f"Booking {result['booking_id']} not found. {refusal_answer()}")
                booking = result["booking"]
                return ModelResponse(text=f"Booking {booking['id']} is {booking['status']}.")
            if item["name"] == "calculate_refund":
                if not result.get("found"):
                    return ModelResponse(text=f"Booking {result['booking_id']} not found. {refusal_answer()}")
                if not result.get("eligible"):
                    return ModelResponse(text=result["message"] + " " + refusal_answer())
                return ModelResponse(text=(
                    f"Total refund: €{result['total_refund_eur']:.2f}. "
                    f"Rental refund: €{result['rental_refund_eur']:.2f}; "
                    f"deposit refund: €{result['deposit_refund_eur']:.2f}; "
                    f"booking fee refunded: €{result['booking_fee_refund_eur']:.2f}. "
                    f"{result['message']}"
                ))
        return ModelResponse(text=refusal_answer())


def refusal_answer() -> str:
    return "I cannot answer from the available CityWheels information. Please contact staff at help@citywheels.example or +48 000 000 000."


def check_case(case: dict[str, Any], answer: str, called_tools: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    actual_tools = [call["name"] for call in called_tools]
    if actual_tools != case["expected_tools"]:
        failures.append(f"tools: expected {case['expected_tools']}, got {actual_tools}")
    answer_lower = answer.lower()
    for required in case["must_contain"]:
        if required.lower() not in answer_lower:
            failures.append(f"missing answer text: {required!r}")
    if case.get("refusal") and "help@citywheels.example" not in answer_lower:
        failures.append("refusal did not direct the customer to staff")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate CityWheels help desk answers.")
    parser.add_argument("--live", action="store_true", help="Use Gemini instead of the offline scenario model.")
    args = parser.parse_args()
    load_environment()
    cases = json.loads((ROOT / "eval" / "questions.json").read_text(encoding="utf-8"))

    rows: list[tuple[str, bool, list[str]]] = []
    model = GeminiModel() if args.live else None
    for case in cases:
        agent = HelpDeskAgent(model if args.live else ScenarioModel(case))
        answer = agent.answer(case["question"])
        failures = check_case(case, answer, agent.last_tool_calls)
        rows.append((case["id"], not failures, failures))

    passed = sum(success for _, success, _ in rows)
    mode = "live Gemini" if args.live else "offline scripted model"
    report = [
        "# Evaluation Results",
        "",
        f"Mode: {mode}",
        f"Result: {passed}/{len(rows)} passed",
        "",
        "The offline mode exercises tool execution, deterministic calculations, and answer checks; it does not measure LLM quality. Use `python eval/run_eval.py --live` to evaluate Gemini tool selection and responses.",
        "",
        "| Question | Result | Details |",
        "| --- | --- | --- |",
    ]
    for question_id, success, failures in rows:
        result = "PASS" if success else "FAIL"
        details = "; ".join(failures) if failures else "All checks passed"
        report.append(f"| {question_id} | {result} | {details} |")
    report_path = ROOT / "eval" / "results.md"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"{passed}/{len(rows)} passed ({mode}); wrote {report_path.relative_to(ROOT)}")
    return 0 if passed == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())