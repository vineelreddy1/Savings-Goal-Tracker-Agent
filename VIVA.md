# Viva Preparation Guide — Savings Goal Tracker Agent

Beginner-friendly, comprehensive answers to key technical questions for the Day 6 Savings Goal Tracker Agent.

---

### 1. What is an AI agent?
An AI agent is an autonomous software program that perceives user input, reasons about goals, formulates plans, executes external tools or functions, observes tool outputs, updates state/memory, and decides subsequent actions to achieve a specific objective. Unlike standard chatbots that generate static text responses, an AI agent takes real actions in system state through tool calls.

### 2. Why is this project agentic?
This project is agentic because it follows an active multi-step reasoning loop:
`USER` $\rightarrow$ `PLAN` $\rightarrow$ `TOOL CALL` $\rightarrow$ `OBSERVE` $\rightarrow$ `MEMORY UPDATE` $\rightarrow$ `DECIDE` $\rightarrow$ `FOLLOW-UP TOOL CALL` $\rightarrow$ `RESPONSE`.
When a user says *"I saved ₹5,000"*, the agent does not merely output text; it understands intent, executes `log_saving(5000)`, stores state in `SavingsMemory`, automatically executes `get_goal_progress()` to calculate progress, evaluates whether the user is `ON_TRACK`, and formulates grounded recommendations based on empirical execution results.

### 3. What are the required tools?
1. `create_savings_goal(target_amount, deadline)`
2. `log_saving(amount)`
3. `get_goal_progress()` (Recommended tool)

### 4. What does `create_savings_goal()` do?
It validates the user's financial target (must be $>0$) and deadline date (must be a valid date format and not in the past relative to the reference date), establishes the goal in `SavingsMemory`, calculates initial required monthly savings, and returns structured status data.

### 5. What does `log_saving()` do?
It validates deposit amounts ($>0$), checks that an active goal exists in memory, appends a timestamped deposit entry `{"amount": amount, "date": date}` to memory, updates the accumulated total saved balance, computes updated remaining target, and returns structured execution results.

### 6. What does `get_goal_progress()` do?
It queries persistent memory to retrieve total savings, target amount, remaining balance, completion percentage, remaining days/months/weeks, expected savings pace, and current goal status (`NOT_STARTED`, `BEHIND`, `ON_TRACK`, `GOAL_REACHED`), returning complete structured metrics.

### 7. How does memory work?
Memory is managed by the `SavingsMemory` class. It maintains persistent state across conversational turns within the agent instance lifecycle. Whenever a tool is called, it modifies or queries `SavingsMemory`, preserving target parameters, deposit records, and turn history across multiple user interactions.

### 8. What information is stored?
- Target savings amount (`target_amount`)
- Deadline date (`deadline`)
- Goal creation date (`creation_date`)
- Configured currency and currency symbol (`currency`, `currency_symbol`)
- Logged savings deposit entries `[{"amount": float, "date": str}]`
- Turn conversation history (`user` and `agent` messages)

### 9. How is progress calculated?
Progress percentage is calculated deterministically in Python as:
$$\text{progress\_percentage} = \left( \frac{\text{total\_saved}}{\text{target}} \right) \times 100$$
If `total_saved >= target`, progress display is capped at `100.0%`.

### 10. How is remaining savings calculated?
Remaining balance is computed deterministically in Python as:
$$\text{remaining} = \max(0.0, \text{target} - \text{total\_saved})$$
This guarantees remaining savings can never become negative.

### 11. How is monthly saving calculated?
The required monthly saving rate is calculated as:
$$\text{required\_monthly\_saving} = \frac{\text{remaining}}{\text{remaining\_months}}$$
where $\text{remaining\_months} = \max\left(1.0, \frac{\text{remaining\_days}}{30.4375}\right)$. If remaining balance is $0$, the monthly requirement is $0.0$.

### 12. How do you determine whether the user is on track?
The agent uses deterministic pace comparison logic:
1. Calculates goal elapsed ratio: $\text{elapsed\_ratio} = \frac{\text{elapsed\_days}}{\text{total\_days}}$.
2. Calculates expected savings pace: $\text{expected\_saved} = \text{target} \times \text{elapsed\_ratio}$.
3. Compares actual saved against expected saved with a 5% tolerance threshold:
   - If $\text{total\_saved} \ge \text{target}$: `GOAL_REACHED`
   - Else if $\text{total\_saved} == 0$: `NOT_STARTED`
   - Else if $\text{total\_saved} \ge \text{expected\_saved} \times (1 - 0.05)$: `ON_TRACK`
   - Else: `BEHIND`

### 13. Why is Python used for calculations?
Large Language Models (LLMs) perform probabilistic text generation and frequently make arithmetic or date calculation errors. Delegating all mathematical formulas, date differences, percentage caps, and status checks to Python ensures 100% mathematical precision and consistency.

### 14. What does the LLM do?
The LLM handles natural language intent understanding, entity extraction (target amounts, deadlines, deposit figures), conversational tool selection, and synthesizing friendly, grounded natural-language responses.

### 15. How does the agent choose tools?
The agent analyzes user input to map intent:
- Intent to set a target $\rightarrow$ `create_savings_goal()`
- Intent to log deposit $\rightarrow$ `log_saving()`
- Intent to query status or progress $\rightarrow$ `get_goal_progress()`
If required parameters (like target or deadline) are missing, the agent asks clarifying questions before calling tools.

### 16. How does the agent use tool results?
Tool results are returned as structured Python dictionaries containing status codes, values, and calculated metrics. The agent inspects these outputs during the **OBSERVE** step and uses them in the **DECIDE** step to format transparent execution logs and formulate factual natural language answers.

### 17. What happens if the deadline is invalid?
If the deadline string cannot be parsed or represents a date in the past relative to the current reference date, `parse_deadline()` returns `(False, None, error_message)`. The tool returns a validation failure without updating memory or crashing, and the agent prompts the user to provide a valid future deadline.

### 18. What happens if the user saves more than the target?
If total saved exceeds the target amount:
- Remaining amount is set to $0.0$.
- Percentage completed display is capped at $100.0\%$.
- Status is evaluated as `GOAL_REACHED`.
- Recommendation provides congratulatory feedback.

### 19. Explain one complete agent execution.
1. **User**: *"I saved ₹5,000."*
2. **Plan**: Detect deposit intent and amount (5000). Formulate plan to log saving.
3. **Tool Call**: Call `log_saving(5000)`.
4. **Tool Result**: Memory adds entry. Returns total saved = ₹5,000, remaining = ₹55,000.
5. **Memory**: State updated with new total deposit and entry timestamp.
6. **Agent Decision**: Decide to query complete goal progress via `get_goal_progress()`.
7. **Tool Call 2**: Call `get_goal_progress()`.
8. **Tool Result 2**: Progress = 8.33%, Status = `ON_TRACK`, Required Monthly = ₹4,599.07.
9. **Final Answer**: *"Recorded ₹5,000! You have saved ₹5,000 of your ₹60,000 goal (8.33% completed). Remaining: ₹55,000. You're on track. Continue saving approximately ₹4,599.07 per month to hit your deadline."*

### 20. How could this project be improved?
- **Database Persistence**: Replace in-memory dictionary storage with SQLite or PostgreSQL database persistence.
- **Multiple Goal Management**: Support multiple concurrent savings goals (e.g. Vacation Fund, Emergency Fund, Laptop Goal).
- **Recurring Auto-Deposits**: Add scheduled recurring deposit logs (e.g., weekly auto-save).
- **Visual Progress Charts**: Generate visual chart images (e.g., Matplotlib/Seaborn trend lines) displaying actual vs. target savings progress over time.
