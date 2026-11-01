"""Google Gemini adapter for the agent's small tool-calling interface."""

from __future__ import annotations

import os
from typing import Any

from .agent import ModelResponse


SYSTEM_INSTRUCTION = """You are the CityWheels customer help desk. Treat the policy documents and booking-tool results as the only source of truth. Use search_policies for policy or shop questions, get_booking for booking details, and calculate_refund for every refund amount. Never calculate a refund yourself or invent missing booking details. If the tools do not contain the answer, or the request is unrelated to CityWheels, say you cannot answer from the available information and direct the customer to help@citywheels.example or +48 000 000 000. Be concise and distinguish the rental refund, deposit, and non-refundable booking fee."""


class GeminiModel:
    def __init__(self, api_key: str | None = None, model_name: str | None = None):
        resolved_key = api_key or os.getenv("GEMINI_API_KEY")
        if not resolved_key:
            raise RuntimeError("GEMINI_API_KEY is not set. Add it to the environment or your .env file.")

        try:
            from google import genai
            from google.genai import types
        except ImportError as error:
            raise RuntimeError("Install project dependencies with: pip install -r requirements.txt") from error

        self.types = types
        self.client = genai.Client(api_key=resolved_key)
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.chat: Any = None

    def start(self, question: str) -> ModelResponse:
        function_declarations = [
            self.types.FunctionDeclaration(
                name="search_policies",
                description="Find relevant sections in CityWheels policy documents.",
                parameters=self.types.Schema(
                    type=self.types.Type.OBJECT,
                    properties={"question": self.types.Schema(type=self.types.Type.STRING)},
                    required=["question"],
                ),
            ),
            self.types.FunctionDeclaration(
                name="get_booking",
                description="Look up a booking by its booking number.",
                parameters=self.types.Schema(
                    type=self.types.Type.OBJECT,
                    properties={"booking_id": self.types.Schema(type=self.types.Type.STRING)},
                    required=["booking_id"],
                ),
            ),
            self.types.FunctionDeclaration(
                name="calculate_refund",
                description="Calculate the cancellation refund for a booking using CityWheels rules and the fixed current date.",
                parameters=self.types.Schema(
                    type=self.types.Type.OBJECT,
                    properties={"booking_id": self.types.Schema(type=self.types.Type.STRING)},
                    required=["booking_id"],
                ),
            ),
        ]
        self.chat = self.client.chats.create(
            model=self.model_name,
            config=self.types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=[self.types.Tool(function_declarations=function_declarations)],
            ),
        )
        return self._parse(self.chat.send_message(question))

    def send_tool_results(self, results: list[dict[str, Any]]) -> ModelResponse:
        if self.chat is None:
            raise RuntimeError("Start a conversation before sending tool results.")
        parts = [
            self.types.Part.from_function_response(name=item["name"], response=item["response"])
            for item in results
        ]
        return self._parse(self.chat.send_message(parts))

    @staticmethod
    def _parse(response: Any) -> ModelResponse:
        calls: list[dict[str, Any]] = []
        text_parts: list[str] = []
        for candidate in response.candidates or []:
            if candidate.content is None:
                continue
            for part in candidate.content.parts or []:
                if part.function_call and part.function_call.name:
                    calls.append({
                        "name": part.function_call.name,
                        "arguments": dict(part.function_call.args or {}),
                    })
                elif part.text:
                    text_parts.append(part.text)
        return ModelResponse(text="\n".join(text_parts).strip() or None, tool_calls=calls)