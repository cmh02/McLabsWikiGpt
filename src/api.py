'''
MCLabs Wiki GPT - Flask API

Author: Chris Hinkson @cmh02
'''

'''
MODULE IMPORTS
'''

# System
import os

# Flask
from flask import Flask, request, jsonify

# Google API
from google import genai

# MCL Packages
from docfetch import WikiEmbedder
from rag import MCL_WikiRag


'''
FLASK APP SETUP
'''

# Initialize Flask app
app = Flask(__name__)

# Gemini client
client = genai.Client(api_key=os.getenv("GOOGLE_GEMINI_API_KEY"))

# Load the index and documents
InstanceWikiEmbedder = WikiEmbedder(client=client)
InstanceWikiEmbedder.loadIndexAndDocuments()

# RAG instance
InstanceRag = MCL_WikiRag(client=client, wikiEmbedder=InstanceWikiEmbedder)


'''
API ENDPOINTS
'''
# Querying RAG via API
@app.route("/query", methods=["POST"])
def query():
    
	# Get the question from the request
    data = request.get_json()
    question = data.get("question")

	# If no question provided, return error
    if not question:
        return jsonify({"error": "Missing 'question'"}), 400

	# Get the response from the RAG pipeline and return
    result, topChunks = InstanceRag.queryPipeline(question)
    return jsonify({"answer": result, "context": topChunks})

if __name__ == "__main__":
    # Railway will inject a $PORT env var
    port = int(os.environ.get("PORT", 5000))
    
    # Host 0.0.0.0 so external requests can reach it in deployment
    app.run(debug=True, host="0.0.0.0", port=port)