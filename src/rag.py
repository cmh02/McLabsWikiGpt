'''
MCLabs Wiki GPT - RAG Prompting and Response

Author: Chris Hinkson @cmh02
'''

'''
MODULE IMPORTS
'''

# System
import os
import dotenv

# Vector Database
import faiss

# Data Handling
import numpy as np

# Google API
from google import genai

# MCL Packages
from docfetch import WikiEmbedder

'''
ENVIRONMENTAL VARIABLES
'''

# Load environment variables from .env file
dotenv.load_dotenv()

# Retrieve the Gemini API key from environment variables
GOOGLE_GEMINI_API_KEY = os.getenv('GOOGLE_GEMINI_API_KEY')

'''
CLIENT SETUP
'''
client = genai.Client(api_key=GOOGLE_GEMINI_API_KEY)

'''
LOAD INDEX AND DOCUMENTS
'''
InstanceWikiEmbedder = WikiEmbedder(client=client)
InstanceWikiEmbedder.loadIndexAndDocuments()

'''
RAG CLASS

This class will handle actually performing RAG prompting and response generation.
'''

class MCL_Wiki_RAG():

	# Class Constructor
	def __init__(self, client: genai.Client=None, wiki_embedder: WikiEmbedder=None):

		# Make client if not provided
		if client is None:
			self.client = genai.Client(api_key=os.getenv('GOOGLE_GEMINI_API_KEY'))
		else:
			self.client = client

		# Load the Wiki Embedder instance
		self.wiki_embedder = InstanceWikiEmbedder

# Embed a user's query using Gemini
def embedQuery(query):
    
	# Get embedding using API
    response = client.models.embed_content(
        model="text-embedding-004",
        contents=[query]
    )
    
    # Return embedding as a numpy float32 vector
    return np.array(response.embeddings[0].values, dtype=np.float32)

# Retrieve top-K relevant chunks from FAISS index
def retrieveChunks(queryVector, topK=5):
    
	# Normalize the query vector and perform the search
    faiss.normalize_L2(queryVector.reshape(1, -1))
    distances, indices = InstanceWikiEmbedder.index.search(queryVector.reshape(1, -1), topK)
    retrieved = [InstanceWikiEmbedder.documents[i] for i in indices[0]]
    
	# Return the retrieved chunks
    return retrieved

# Generate an answer using Gemini with the retrieved chunks as context
def generateAnswer(question, topChunks):
    
	# Combine chunks into context and create the prompt
    contextText = "\n".join([f"{chunk['title']}: {chunk['content']}" for chunk in topChunks])
    prompt = f"""
    Use the following wiki content to answer the question:
	\n{contextText}
    \n\nQuestion: {question}
    \nAnswer:"
    """
    
	# Get the answer using the API
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt
    )
    
	# Return the generated answer text
    return response.text

# Full pipeline function to handle a user query
def queryPipeline(question, topK=5):
    
    # Embed the query
    queryVector = embedQuery(question)
    
	# Retriev top-K chunks
    topChunks = retrieveChunks(queryVector, topK=topK)
    
	# Generate the answer
    answer = generateAnswer(question, topChunks)
    
	# Return the answer and the top chunks used
    return answer, topChunks


if __name__ == "__main__":
	question = "How do I claim land on the server?"
	answer, chunks = queryPipeline(question, topK=5)

	print("\nQuestion:\n", question)
	print("\nAnswer:\n", answer)
	print("\nSources:")
	for chunk in chunks:
		print("-", chunk["title"])