# Day 6 — Savings Goal Tracker Agent

An intelligent, production-grade AI Agent designed to help users establish financial savings targets, record deposits, monitor progress, evaluate pace (`NOT_STARTED`, `BEHIND`, `ON_TRACK`, `GOAL_REACHED`), and receive grounded guidance over time.

---

## Objective

Build an AI agent that:
1. **Parses financial intents & target deadlines** from natural user conversations (e.g., *"I want to save ₹60,000 by December"*).
2. **Executes financial tools** to register goals, store deposit entries, and compute progress metrics.
3. **Delegates arithmetic and date math to Python**, ensuring exact mathematical accuracy without LLM calculation errors.
4. **Maintains persistent cross-turn memory** across multiple savings deposits and conversational turns.
5. **Provides visible agent execution traces** (`[USER]`, `[AGENT PLAN]`, `[TOOL CALL]`, `[TOOL RESULT]`, `[MEMORY]`, `[AGENT DECISION]`, `[FINAL ANSWER]`).

---

## Features

- **Deterministic Financial Math**: Remaining amount, percentage completion (capped at 100%), time metrics (days, weeks, months), and required monthly saving rates are computed in pure Python.
- **Pace & On-Track Evaluation**: Evaluates expected progress against actual progress using elapsed timeline ratios and tolerance thresholds (`NOT_STARTED`, `BEHIND`, `ON_TRACK`, `GOAL_REACHED`).
- **Multiple Deposit Logging**: Accumulates savings deposits over time while recording timestamped entries (`{"amount": 5000, "date": "2026-01-05"}`).
- **Robust Input Validation**: Rejects invalid targets ($\le 0$), negative deposit amounts, past deadlines, and improper date formats without crashing.
- **Keyless & Offline Reliability**: Includes an LLM-first intent analyzer backed by a deterministic regex parser fallback, allowing tests and notebooks to execute 100% reliably anywhere.

---

## Architecture & Agentic Loop

The architecture follows a multi-step Plan-Act-Observe-Decide cycle:

```
                    USER
                      │
                      ▼
                    AGENT
                      │
                 PLAN INTENT
                      │
       ┌──────────────┴──────────────┐
       ▼                             ▼
create_savings_goal()           log_saving()
       │                             │
       └──────────────┬──────────────┘
                      ▼
                    MEMORY
                      │
             get_goal_progress()
                      │
       ┌──────────────┴──────────────┐
       ▼                             ▼
   PROGRESS                        STATUS
       └──────────────┬──────────────┘
                      ▼
                RECOMMENDATION
                      │
                      ▼
                FINAL RESPONSE
```

### Agentic Loop Steps:
1. **USER**: Natural language input (e.g., *"I saved ₹5,000"*).
2. **AGENT PLAN**: Formulates actionable intent and identifies required tools.
3. **TOOL CALL**: Invokes structured Python tools (`log_saving(5000)`).
4. **TOOL RESULT**: Observes tool output (Total saved = ₹5,000, Remaining = ₹55,000).
5. **MEMORY**: Updates persistent state (`SavingsMemory`).
6. **AGENT DECISION**: Determines follow-up actions (e.g., executing `get_goal_progress()` to verify on-track status).
7. **FINAL ANSWER**: Formulates a clear, grounded response with calculated metrics and recommendations.

---

## Tools Specification

### 1. `create_savings_goal(target_amount, deadline)`
Configures a new financial savings goal in memory.
```json
{
  "success": true,
  "target": 60000.0,
  "deadline": "2026-12-31",
  "required_monthly_saving": 4599.07,
  "currency_symbol": "₹"
}
```

### 2. `log_saving(amount)`
Records a deposit into persistent memory state.
```json
{
  "success": true,
  "amount_added": 5000.0,
  "total_saved": 5000.0,
  "remaining": 55000.0,
  "percentage": 8.33,
  "status": "ON_TRACK"
}
```

### 3. `get_goal_progress()`
Queries full goal progress metrics, remaining duration, on-track status, and recommendations.
```json
{
  "target": 60000.0,
  "saved": 10000.0,
  "remaining": 50000.0,
  "percentage": 16.67,
  "deadline": "2026-12-31",
  "required_monthly_saving": 4348.21,
  "status": "ON_TRACK",
  "recommendation": "You're on track. Continue saving approximately ₹4,348.21 per month to hit your deadline."
}
```

---

## Persistent Memory (`SavingsMemory`)

The agent retains state across conversation turns:
- `target_amount`: Target savings goal in currency units.
- `deadline`: Target completion date (`YYYY-MM-DD`).
- `creation_date`: Date the goal was established.
- `savings_entries`: List of logged savings deposits `[{"amount": float, "date": str}]`.
- `total_saved`: Sum of all logged amounts.
- `remaining`: `max(0.0, target - total_saved)`.
- `conversation_history`: Turn history (`user` and `agent` messages).

---

## Deterministic Calculation Engine

To prevent LLM hallucination and arithmetic errors:
1. **Total Saved**: Calculated by `sum(entry["amount"] for entry in savings_entries)`.
2. **Remaining Amount**: Computed as `max(0.0, target - total_saved)`.
3. **Percentage Completed**: `(total_saved / target) * 100`, capped at `100.0%` for status display.
4. **Required Monthly Saving**: `remaining / remaining_months` where `remaining_months = remaining_days / 30.4375`.
5. **On-Track Status**:
   - `expected_saved = target * (elapsed_days / total_days)`
   - Status is `GOAL_REACHED` if `total_saved >= target`.
   - Status is `NOT_STARTED` if `total_saved == 0`.
   - Status is `ON_TRACK` if `total_saved >= expected_saved * (1 - tolerance)`.
   - Otherwise `BEHIND`.

---

## Error Handling & Validation

- **Invalid Target**: Rejects $\le 0$ targets with explanatory messages.
- **Invalid / Past Deadline**: Validates format (`YYYY-MM-DD`, `Month Year`) and ensures deadline is not in the past relative to reference date.
- **Missing Goal**: Prevents logging savings when no active goal exists.
- **Invalid Saving Amount**: Rejects amounts $\le 0$.
- **Underspecified Input**: Prompts user for missing targets or deadlines.

---

## Honest Failure

**Problem Encountered**:
During initial testing of intent parsing, queries like *"How much have I saved?"* triggered a false match for `LOG_SAVING` with missing amount (`CLARIFICATION_NEEDED`). This occurred because the intent classification rule checked for the keyword `"saved"` inside deposit logging logic *before* evaluating query intents (`CHECK_PROGRESS`).

**Fix Applied**:
Re-structured the intent evaluation sequence in `agent.py` so that progress and remaining queries (`CHECK_PROGRESS`, `CHECK_REMAINING`) are evaluated *prior* to deposit logging logic. This ensured that question queries containing the past-tense word `"saved"` correctly route to `get_goal_progress()` instead of asking for deposit amounts.

---

## Installation & Running

### Installation
```bash
cd savings-goal-agent
pip install -r requirements.txt
```

### Running Test Suite
```bash
pytest tests/ -v
```

### Running Demo Runner Script
```bash
python notebook/demo_runner.py
```

### Running Jupyter Notebook Demo
```bash
jupyter notebook notebook/savings_goal_demo.ipynb
```

---

## Example Interaction

```text
[USER]
I want to save ₹60,000 by December.

[AGENT PLAN]
Create savings goal with target 60000.0 and deadline 'December'.

[TOOL CALL]
create_savings_goal(target_amount=60000.0, deadline='December')

[TOOL RESULT]
{
  "success": true,
  "target": 60000.0,
  "deadline": "2026-12-31",
  "required_monthly_saving": 4599.07
}

[AGENT DECISION]
Savings goal stored in memory. Retrieving initial monthly pace.

[FINAL ANSWER]
✅ Your savings goal of ₹60,000 by 2026-12-31 has been created! To stay on track, you'll need to save approximately ₹4,599.07 per month.
```

---

## Limitations

1. **Single Active Goal**: The current implementation tracks one primary savings goal per memory instance.
2. **Fixed Inflation / Interest Rate**: Arithmetic assumes flat target savings without interest accrual or inflation adjustments.
3. **Local In-Memory Persistence**: Session memory is maintained in-memory per agent lifecycle (can be backed by SQLite/JSON in future iterations).
