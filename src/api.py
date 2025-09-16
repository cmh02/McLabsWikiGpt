'''
MCLabs Wiki GPT - Flask API

Author: Chris Hinkson @cmh02
'''

'''
MODULE IMPORTS
'''

# System
import os
import time
from datetime import datetime, timedelta, timezone

# Flask
import gunicorn
from flask import Flask, request, jsonify

# Google API
from google import genai

# MCL Packages
from docfetch import MCL_WikiEmbedder
from rag import MCL_WikiRag

'''
FLASK APP SETUP
'''

# Initialize Flask app
app = Flask(__name__)

# Load environment variables from .env file if not in Railway environment
if os.getenv("RAILWAY_ENVIRONMENT_ID") is None:
    from dotenv import load_dotenv
    load_dotenv()

# Gemini client
client = genai.Client(api_key=os.getenv("GOOGLE_GEMINI_API_KEY"))

# Load the index and documents
InstanceWikiEmbedder = MCL_WikiEmbedder(client=client)
InstanceWikiEmbedder.loadIndexAndDocuments()

# RAG instance
InstanceRag = MCL_WikiRag(client=client, wikiEmbedder=InstanceWikiEmbedder)

# API Limits
MAX_REQUESTS_PER_MINUTE = 15
MAX_REQUESTS_PER_DAY = 1000

'''
API LIMITING
'''

# Track request counts (minutes reset at top of minute, day resets at midnight pacific time)
requestCounts = {
    "minute": 0,
    "day": 0,
    "minuteReset": datetime.now().replace(second=0, microsecond=0) + timedelta(minutes=1),
    "dayReset": datetime.now().replace(hour=7, minute=0, second=0, microsecond=0)
}

# Check and update request counts
def api_checkLimits():
    
	# Get needed info
    global requestCounts
    now = datetime.now()

    # Reset per-minute counter at the top of the minute
    if now >= requestCounts["minuteReset"]:
        requestCounts["minute"] = 0
        requestCounts["minuteReset"] = now.replace(second=0, microsecond=0) + timedelta(minutes=1)

    # Reset per-day counter at midnight PT (07:00 UTC)
    if now >= requestCounts["dayReset"]:
        requestCounts["day"] = 0
        requestCounts["dayReset"] = now.replace(hour=7, minute=0, second=0, microsecond=0) + timedelta(days=1)

    # Check if we’re over limits
    if requestCounts["minute"] >= MAX_REQUESTS_PER_MINUTE:
        return False, f"Rate limit exceeded: {MAX_REQUESTS_PER_MINUTE} requests per minute", 1
    if requestCounts["day"] >= MAX_REQUESTS_PER_DAY:
        return False, f"Rate limit exceeded: {MAX_REQUESTS_PER_DAY} requests per day", 2

    # Count this request and allow
    requestCounts["minute"] += 1
    requestCounts["day"] += 1
    return True, None, 0

@app.before_request
def api_limitRequests():
    print("test")
    ok, errorMessage, errorCode = api_checkLimits()
    if not ok:
        return jsonify({"errormessage": errorMessage, "errorcode": errorCode}), 429

'''
API ENDPOINTS
'''
# Querying RAG via API
@app.route("/query", methods=["POST"])
def query():

	print("test2")

	# Get the question from the request
	data = request.get_json()
	question = data.get("question")

	# Print for debugging
	if os.environ.get("MCL_DEBUG", "FALSE") == "TRUE":
		print(f"Received question: {question}")

	# If no question provided, return error
	if not question:
		return jsonify({"error": "Missing 'question'"}), 400

	# If question is too long, return error
	if len(question) > 256:
		return jsonify({"errormessage": "Question is too long (max 256 characters)!", "errorcode": 3}), 400

	# Print for debugging
	if os.environ.get("MCL_DEBUG", "FALSE") == "TRUE":
		print(f"Answer to question {question}: {result}")	

	# Get the response from the RAG pipeline and return
	result, topChunks = InstanceRag.queryPipeline(question)
	return jsonify({"answer": result, "context": topChunks})

if __name__ == "__main__":
    # Railway will inject a $PORT env var
    print(f"Starting application on port {os.environ.get('PORT')}!")