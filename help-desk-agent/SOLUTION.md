# CityWheels Help Desk Agent

## Install and run

Use Python 3.10 or newer. From the project directory:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `GEMINI_API_KEY` in `.env`, then ask a one-off question or start an interactive session:

```bash
python -m citywheels "What time do you open on Saturday?"
python -m citywheels
```

Run the unit tests with `python -m unittest discover -s tests -v`. Run the offline evaluation with `python eval/run_eval.py`, or evaluate Gemini itself with `python eval/run_eval.py --live`.

## Model and design

The live adapter uses Google's Gemini API through the official `google-genai` SDK, with `gemini-2.5-flash` as the default. The API offers a free tier subject to Google's current model availability and quotas; no paid account is assumed. The API key remains in an environment variable. The agent manually handles the tool-call loop: it sends a question, executes each requested function locally, returns function results to Gemini, and repeats until Gemini provides a final answer.

The tools search Markdown policy sections, look up exact booking IDs in the supplied JSON, and calculate refunds in Python. Refund amounts use the assignment's fixed timestamp, so they are repeatable. The model instruction requires source-grounded answers, delegates all refund arithmetic to code, and tells the model to refer unsupported questions to staff.

## Evaluation

The question set covers policy facts, booking lookup, all three cancellation windows, voucher refunds, an unknown booking, and questions CityWheels cannot answer. The committed run in `eval/results.md` uses an offline scripted model: it verifies the tools, refund arithmetic, and answer checks without a key or network, but does not measure Gemini's quality. Run the live mode to assess model tool selection and wording. The checks are deliberately literal and may miss semantically correct paraphrases.

## AI coding assistance

GitHub Copilot was used to draft the Python tool, agent, and test structure. The first generated project patch did not create nested package directories, so test discovery failed before any tests ran. I created the directories explicitly and reran the focused unit suite before continuing. This reinforced the need to verify generated changes in the actual project root rather than treating a patch response as proof that files landed.

## Limitations and next steps

Policy search uses lightweight token overlap rather than semantic retrieval, and the example booking file is not an authenticated or live booking system. The model can also misunderstand a question or phrase a sourced fact poorly; live evaluation and human review remain important. With more time, I would expand evaluation using real model runs, add conversation memory with explicit booking-context checks, and improve retrieval while keeping citations to the source sections.