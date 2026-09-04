"""
Agent Module for Savings Goal Tracker Agent.
Implements the Agentic Plan -> Act -> Observe -> Decide loop, visible execution trace,
tool invocation, persistent memory integration, and natural language synthesis.
"""

import json
import re
import os
from datetime import date
from typing import Dict, Any, List, Optional, Tuple

from memory import SavingsMemory
import tools
from savings_logic import format_currency
from config import DEFAULT_REFERENCE_DATE, VERBOSE_TRACE


class TraceLogger:
    """Helper class to record and print visible agent execution traces."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.logs: List[str] = []

    def log(self, tag: str, content: str) -> None:
        formatted = f"[{tag}]\n{content.strip()}\n"
        self.logs.append(formatted)
        if self.verbose:
            try:
                print(formatted)
            except Exception:
                safe_str = formatted.encode("ascii", errors="replace").decode("ascii")
                print(safe_str)

    def get_full_trace(self) -> str:
        return "\n".join(self.logs)


class SavingsGoalAgent:
    """
    SavingsGoalAgent:
    An agentic AI financial assistant that creates savings goals, logs savings,
    evaluates pace deterministically in Python, maintains cross-turn memory,
    and logs visible execution traces.
    """

    def __init__(
        self,
        memory: Optional[SavingsMemory] = None,
        ref_date: Optional[date] = None,
        verbose: bool = True
    ):
        self.ref_date = ref_date if ref_date is not None else DEFAULT_REFERENCE_DATE
        self.memory = memory if memory is not None else SavingsMemory(ref_date=self.ref_date)
        self.verbose = verbose

    def process_turn(self, user_message: str) -> Dict[str, Any]:
        """
        Executes a complete multi-step Plan-Act-Observe-Decide turn for a user message.
        """
        logger = TraceLogger(verbose=self.verbose)
        logger.log("USER", user_message)

        # Record user message in history
        self.memory.add_history("user", user_message)

        # Run agent loop
        final_answer = self._run_plan_act_loop(user_message, logger)

        # Record memory state & agent answer in history
        self.memory.add_history("agent", final_answer)
        logger.log("MEMORY", self.memory.get_memory_summary())

        return {
            "user_message": user_message,
            "final_answer": final_answer,
            "trace_log": logger.get_full_trace(),
            "progress": self.memory.get_progress(ref_date=self.ref_date)
        }

    def _run_plan_act_loop(self, user_message: str, logger: TraceLogger) -> str:
        """
        Executes the core Plan -> Act -> Observe -> Decide agent loop.
        """
        clean_msg = user_message.strip()

        # Step 1: Intent & Entity Parsing
        parsed_intent = self._analyze_intent(clean_msg)
        action_type = parsed_intent["action_type"]
        plan_str = parsed_intent["plan"]

        logger.log("AGENT PLAN", plan_str)

        # Handle missing information / required clarification
        if action_type == "CLARIFICATION_NEEDED":
            logger.log("AGENT DECISION", "User request is underspecified. Requesting clarification.")
            final_ans = parsed_intent["clarification_msg"]
            logger.log("FINAL ANSWER", final_ans)
            return final_ans

        # Case 1: CREATE SAVINGS GOAL
        if action_type == "CREATE_GOAL":
            target = parsed_intent.get("target_amount")
            deadline = parsed_intent.get("deadline")

            logger.log("TOOL CALL", f"create_savings_goal(target_amount={target}, deadline='{deadline}')")
            goal_res = tools.create_savings_goal(
                target_amount=target,
                deadline=deadline,
                memory=self.memory,
                ref_date=self.ref_date
            )
            logger.log("TOOL RESULT", json.dumps(goal_res, indent=2))

            if not goal_res.get("success"):
                err = goal_res.get("error", "Failed to create savings goal.")
                logger.log("AGENT DECISION", f"Tool create_savings_goal failed validation: {err}")
                final_ans = f"⚠️ {err}"
                logger.log("FINAL ANSWER", final_ans)
                return final_ans

            # Goal created successfully. Now decide to fetch progress details.
            logger.log("AGENT DECISION", "Savings goal stored in memory. Retrieving initial monthly pace.")
            prog = self.memory.get_progress(ref_date=self.ref_date)

            sym = prog["currency_symbol"]
            target_fmt = format_currency(prog["target"], sym)
            monthly_fmt = format_currency(prog["required_monthly_saving"], sym)

            final_ans = (
                f"✅ Your savings goal of {target_fmt} by {prog['deadline']} has been created! "
                f"To stay on track, you'll need to save approximately {monthly_fmt} per month."
            )
            logger.log("FINAL ANSWER", final_ans)
            return final_ans

        # Case 2: LOG SAVING
        if action_type == "LOG_SAVING":
            amount = parsed_intent.get("amount")

            logger.log("TOOL CALL", f"log_saving(amount={amount})")
            save_res = tools.log_saving(
                amount=amount,
                memory=self.memory,
                ref_date=self.ref_date
            )
            logger.log("TOOL RESULT", json.dumps(save_res, indent=2))

            if not save_res.get("success"):
                err = save_res.get("error", "Failed to log saving.")
                logger.log("AGENT DECISION", f"Tool log_saving returned validation error: {err}")
                final_ans = f"⚠️ {err}"
                logger.log("FINAL ANSWER", final_ans)
                return final_ans

            # Step 2: Agent Decides to check progress after logging
            logger.log("AGENT DECISION", "Savings recorded. Now querying goal progress to evaluate on-track status.")

            logger.log("TOOL CALL", "get_goal_progress()")
            prog_res = tools.get_goal_progress(
                memory=self.memory,
                ref_date=self.ref_date
            )
            logger.log("TOOL RESULT", json.dumps(prog_res, indent=2))

            sym = prog_res["currency_symbol"]
            added_fmt = format_currency(save_res["amount_added"], sym)
            total_fmt = format_currency(prog_res["saved"], sym)
            target_fmt = format_currency(prog_res["target"], sym)

            pct = prog_res["percentage"]
            status = prog_res["status"]
            rec = prog_res["recommendation"]

            if status == "GOAL_REACHED":
                final_ans = f"🎉 Recorded {added_fmt}! You have saved a total of {total_fmt} of your {target_fmt} goal ({pct}%). {rec}"
            else:
                rem_fmt = format_currency(prog_res["remaining"], sym)
                final_ans = (
                    f"Recorded {added_fmt}! You have saved {total_fmt} of your {target_fmt} goal ({pct}% completed). "
                    f"Remaining: {rem_fmt}. {rec}"
                )

            logger.log("FINAL ANSWER", final_ans)
            return final_ans

        # Case 3: CHECK PROGRESS
        if action_type == "CHECK_PROGRESS":
            logger.log("TOOL CALL", "get_goal_progress()")
            prog_res = tools.get_goal_progress(
                memory=self.memory,
                ref_date=self.ref_date
            )
            logger.log("TOOL RESULT", json.dumps(prog_res, indent=2))

            if not prog_res.get("active_goal"):
                logger.log("AGENT DECISION", "No active goal in memory. Informing user.")
                final_ans = "You don't have an active savings goal yet. Set one by saying e.g. 'I want to save ₹60,000 by December'."
                logger.log("FINAL ANSWER", final_ans)
                return final_ans

            logger.log("AGENT DECISION", "Progress metrics retrieved. Formulating comprehensive summary.")

            sym = prog_res["currency_symbol"]
            saved_fmt = format_currency(prog_res["saved"], sym)
            target_fmt = format_currency(prog_res["target"], sym)
            rem_fmt = format_currency(prog_res["remaining"], sym)
            pct = prog_res["percentage"]
            rec = prog_res["recommendation"]

            final_ans = (
                f"📊 Progress Summary:\n"
                f"• Saved: {saved_fmt} of {target_fmt} ({pct}%)\n"
                f"• Remaining: {rem_fmt}\n"
                f"• Deadline: {prog_res['deadline']}\n"
                f"• Status: {prog_res['status']}\n"
                f"💡 {rec}"
            )
            logger.log("FINAL ANSWER", final_ans)
            return final_ans

        # Case 4: CHECK REMAINING
        if action_type == "CHECK_REMAINING":
            logger.log("TOOL CALL", "get_goal_progress()")
            prog_res = tools.get_goal_progress(
                memory=self.memory,
                ref_date=self.ref_date
            )
            logger.log("TOOL RESULT", json.dumps(prog_res, indent=2))

            if not prog_res.get("active_goal"):
                logger.log("AGENT DECISION", "No active goal found. Informing user.")
                final_ans = "You haven't configured a savings goal yet. Set one first!"
                logger.log("FINAL ANSWER", final_ans)
                return final_ans

            logger.log("AGENT DECISION", "Focusing response on remaining target math.")
            sym = prog_res["currency_symbol"]
            rem_fmt = format_currency(prog_res["remaining"], sym)
            target_fmt = format_currency(prog_res["target"], sym)
            monthly_fmt = format_currency(prog_res["required_monthly_saving"], sym)

            if prog_res["status"] == "GOAL_REACHED":
                final_ans = f"You have fully reached your savings goal of {target_fmt}! Remaining amount is {rem_fmt}."
            else:
                final_ans = (
                    f"You need to save {rem_fmt} more to reach your goal of {target_fmt}. "
                    f"That requires approximately {monthly_fmt} per month."
                )

            logger.log("FINAL ANSWER", final_ans)
            return final_ans

        # Default Fallback
        logger.log("AGENT DECISION", "Could not map query to specific tool action. Providing general guidance.")
        final_ans = "I am your Savings Goal Agent. You can tell me to set a goal (e.g. 'I want to save ₹60,000 by December'), log a saving (e.g. 'I saved ₹5,000'), or ask about your progress!"
        logger.log("FINAL ANSWER", final_ans)
        return final_ans

    def _analyze_intent(self, text: str) -> Dict[str, Any]:
        """
        Analyzes user input using deterministic regex extraction with rule fallback.
        Ensures offline capability while accurately detecting goals, savings logs, and progress queries.
        """
        text_lower = text.lower()

        # 1. Detect Goal Creation intent
        # Looks for patterns like "want to save 60000 by december" or "target 50000 deadline 2026-12-31"
        is_goal_intent = any(k in text_lower for k in [
            "want to save", "target of", "set a goal", "goal of", "save ₹", "save rs", "save $"
        ]) and ("by" in text_lower or "until" in text_lower or "deadline" in text_lower or "december" in text_lower or "202" in text_lower)

        # 2. Extract numbers
        amounts = re.findall(r"(?:₹|rs\.?|\$)?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?|\d+)", text, re.IGNORECASE)
        # Clean commas from parsed numbers
        cleaned_numbers = []
        for a in amounts:
            try:
                num = float(a.replace(",", ""))
                cleaned_numbers.append(num)
            except ValueError:
                pass

        # 1. Goal creation intent: target + deadline
        if is_goal_intent or ("save" in text_lower and ("by" in text_lower or "until" in text_lower or "deadline" in text_lower)):
            target_amount = cleaned_numbers[0] if cleaned_numbers else None
            deadline_match = re.search(r"(?:by|until|deadline|before)\s+([a-zA-Z0-9\s,-]+)", text, re.IGNORECASE)
            deadline_str = deadline_match.group(1).strip() if deadline_match else None

            if deadline_str:
                deadline_str = re.split(r"[.!?]", deadline_str)[0].strip()

            if target_amount is None and deadline_str is None:
                return {
                    "action_type": "CLARIFICATION_NEEDED",
                    "plan": "Goal creation request missing both target amount and deadline.",
                    "clarification_msg": "Please specify both your target savings amount and deadline (e.g., 'I want to save ₹60,000 by December')."
                }
            elif target_amount is None:
                return {
                    "action_type": "CLARIFICATION_NEEDED",
                    "plan": "Goal creation request missing target savings amount.",
                    "clarification_msg": "Please specify how much money you want to save."
                }
            elif deadline_str is None:
                return {
                    "action_type": "CLARIFICATION_NEEDED",
                    "plan": "Goal creation request missing deadline.",
                    "clarification_msg": "Please specify a target deadline date (e.g., 'by December 2026')."
                }

            return {
                "action_type": "CREATE_GOAL",
                "plan": f"Create savings goal with target {target_amount} and deadline '{deadline_str}'.",
                "target_amount": target_amount,
                "deadline": deadline_str
            }

        # 2. Check remaining amount & progress queries
        if any(k in text_lower for k in ["how much more", "need to save", "remaining", "left to save", "how much left"]):
            return {
                "action_type": "CHECK_REMAINING",
                "plan": "Query persistent memory to calculate remaining savings needed."
            }

        if any(k in text_lower for k in ["how much have i saved", "how much i saved", "how much saved", "progress", "status", "summary", "total saved", "how am i doing", "how much have i"]):
            return {
                "action_type": "CHECK_PROGRESS",
                "plan": "Query goal progress metrics and evaluate on-track status."
            }

        # 3. Log savings: "I saved 5000", "saved another 3000", "added 2000 to savings"
        if ("saved" in text_lower or "log" in text_lower or "add" in text_lower or "deposited" in text_lower) and not is_goal_intent:
            if cleaned_numbers:
                amt = cleaned_numbers[0]
                return {
                    "action_type": "LOG_SAVING",
                    "plan": f"Record user saving entry of {amt} into persistent goal memory.",
                    "amount": amt
                }
            elif "save" in text_lower:
                return {
                    "action_type": "CLARIFICATION_NEEDED",
                    "plan": "User wants to log savings but amount is missing.",
                    "clarification_msg": "Please specify how much money you saved (e.g., 'I saved ₹5,000')."
                }

        # If user provides just a number after goal is created
        if cleaned_numbers and len(cleaned_numbers) == 1 and ("save" in text_lower or "saved" in text_lower):
            amt = cleaned_numbers[0]
            if self.memory.has_active_goal():
                return {
                    "action_type": "LOG_SAVING",
                    "plan": f"Record user saving entry of {amt}.",
                    "amount": amt
                }

        # Fallback query
        return {
            "action_type": "GENERAL_QUERY",
            "plan": "Provide assistant overview and capabilities."
        }
