"""
Flask Web Application for Savings Goal Tracker Agent.
Provides web dashboard and REST API endpoints.
"""

import os
from datetime import date
from flask import Flask, render_template, request, jsonify

from agent import SavingsGoalAgent
from config import DEFAULT_REFERENCE_DATE

app = Flask(__name__)

# Initialize agent instance with default reference date
agent = SavingsGoalAgent(ref_date=date.today(), verbose=True)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json or {}
    user_message = data.get("message", "").strip()
    
    if not user_message:
        return jsonify({"error": "Message cannot be empty"}), 400

    result = agent.process_turn(user_message)
    return jsonify(result)

@app.route("/api/progress", methods=["GET"])
def get_progress():
    progress = agent.memory.get_progress(ref_date=agent.ref_date)
    return jsonify(progress)

@app.route("/api/reset", methods=["POST"])
def reset_memory():
    agent.memory.reset()
    return jsonify({"success": True, "message": "Memory reset successfully."})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"* Starting Savings Goal Tracker Agent Web Server on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
