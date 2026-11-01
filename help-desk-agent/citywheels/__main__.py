"""Command-line entry point."""

from __future__ import annotations

import argparse

from .agent import HelpDeskAgent
from .config import load_environment
from .gemini import GeminiModel


def main() -> None:
    load_environment()
    parser = argparse.ArgumentParser(description="Ask the CityWheels help desk.")
    parser.add_argument("question", nargs="*", help="Customer question; omit to start an interactive session.")
    args = parser.parse_args()
    agent = HelpDeskAgent(GeminiModel())

    if args.question:
        print(agent.answer(" ".join(args.question)))
        return

    print("CityWheels help desk. Type 'exit' to quit.")
    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if question.lower() in {"exit", "quit"}:
            break
        if question:
            print(f"CityWheels: {agent.answer(question)}")


if __name__ == "__main__":
    main()