# Recruitment Assignment - Help Desk Agent

## Context

CityWheels is a small, made-up bike rental shop. Its customers keep asking the same things: opening hours, prices, what happens when they cancel, how much money they get back. CityWheels wants an AI agent that answers these questions from the shop's own rules and booking data.

Together with this description you get a ZIP file, `citywheels-help-desk.zip`. It contains only data, no code:

- `data/policies/` — the shop's rules as Markdown files: prices, cancellations and refunds, frequently asked questions.
- `data/bookings.json` — example bookings.
- `README.md` — what the files mean, and the fixed "current date" to use.

**Before starting the assignment, create your own repository on GitHub and add the files from the ZIP file as your starting point. Do not include the assignment instructions you received in your repository.** The repository can be public, or private: then add `cf-recruitment` as a collaborator (Settings → Collaborators → Add people), so we can read it. You can remove it once the recruitment ends.

Complete the entire assignment in your own repository. **You have a maximum of 3 days from receiving the assignment to complete it. We expect it to take about 6–8 hours.** Once finished, email a link to your repository to [careers@cloudfide.com](mailto:careers@cloudfide.com).

We do not expect a perfect or large solution. We want to see how you think, how quickly you learn, and how you check that an AI system does what it should.

## Task

Build a **command-line AI agent** that answers customer questions for CityWheels.

Use **Python** (preferred) or **Java**.

### The agent

- The agent uses a large language model (LLM) with **tool calling**: the model decides which tool to call, your code runs the tool and gives the result back to the model, and this repeats until the model gives a final answer.
- You may use any LLM provider. You do not need to pay for one: free options include the Google Gemini API free tier, GitHub Models, or a local model with Ollama. You may call the provider's API directly or use a framework (for example LangChain, LangGraph or Semantic Kernel), as long as you can explain what it does for you.
- A user can ask a question from the command line and get an answer.
- The API key is read from an environment variable. The repository includes a `.env.example` file with the names of the variables you need, and **no real keys or secrets**.

### The tools

Write at least these three tools yourself:

- `search_policies` — finds the parts of the documents in `data/policies/` that are relevant to a question.
- `get_booking` — returns the details of one booking from `data/bookings.json`, or a clear "not found" result when the booking does not exist.
- `calculate_refund` — calculates how much a customer gets back if they cancel a booking now, following the cancellation rules. **The amount must be calculated by your code, not by the model.**

You may add more tools if you think they help.

### The behavior

- Answers are based on the CityWheels documents and bookings, not on the model's general knowledge.
- The agent never makes up booking details or amounts.
- When the documents and bookings do not answer a question, or the question has nothing to do with CityWheels, the agent says so and tells the customer to contact the staff.
- A wrong or unknown booking number does not crash the program; the agent tells the customer the booking was not found.

### Tests

- Write unit tests for your tools, including each rule of `calculate_refund`.
- Write at least one test of the agent loop that uses a fake model instead of a real one, so it needs no network and no API key.
- All tests run with a single command.

### Evaluation

An agent is only useful when you know how well it works. Build a small evaluation:

- A file with **at least 10 test questions**, each with the expected outcome (for example: which tool should be called, what amount or fact the answer must contain, or that the agent must refuse).
- Include at least 2 questions that need a refund calculation and at least 2 questions the agent should not answer.
- A script that runs the agent on all the questions and checks the answers automatically where it can.
- Commit the results of your last evaluation run to the repository, for example as `eval/results.md`, with how many questions passed.

It is fine if some questions fail. We care more about an honest result and a good explanation than about a perfect score.

## Extras

These are optional. Do them only if you have time left:

- A GitHub Actions workflow that runs your tests on every push.
- Conversation memory, so a customer can ask follow-up questions (for example "and what if I cancel tomorrow instead?").
- A comparison of two approaches, for example calling the API directly versus using a framework, or two different models, with what you found.

## Documentation

Include a short `SOLUTION.md` file describing:

- how to install and run the agent, the tests and the evaluation,
- which model and provider you chose, and why,
- how your agent works: the loop, the tools and the instructions you give the model,
- your evaluation results: what failed, why you think it failed, and what you tried to fix,
- how you used AI coding assistants (for example GitHub Copilot, Claude or ChatGPT) while building this, including at least one example where their output was wrong or needed changes, and how you noticed,
- the limitations of your solution,
- what you would do next with more time.

## Follow-up

Be prepared to walk through your solution in a follow-up conversation, explain your decisions, and make a small change to it live.
