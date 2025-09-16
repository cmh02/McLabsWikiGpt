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

class MCL_WikiRag():

	# Class Constructor
	def __init__(self, client: genai.Client=None, wikiEmbedder: WikiEmbedder=None):

		# Make client if not provided
		if client is None:
			self.client = genai.Client(api_key=os.getenv('GOOGLE_GEMINI_API_KEY'))
		else:
			self.client = client

		# Make WikiEmbedder instance if not provided
		if wikiEmbedder is None:
			self.wikiEmbedder = WikiEmbedder(client=self.client)
		else:
			self.wikiEmbedder = wikiEmbedder

	# Full pipeline function to handle a user query
	def queryPipeline(self, question, topK=5) -> tuple:
		
		# Embed the query
		queryVector = self._embedQuery(question)
		
		# Retriev top-K chunks
		topChunks = self._retrieveChunks(queryVector, topK=topK)

		# Generate the answer
		answer = self._generateAnswer(question, topChunks)

		# Return the answer and the top chunks used
		return answer, topChunks

	# Embed a user's query using Gemini
	def _embedQuery(self, query) -> np.ndarray:
		
		# Get embedding using API
		response = self.client.models.embed_content(
			model="text-embedding-004",
			contents=[query]
		)
		
		# Return embedding as a numpy float32 vector
		return np.array(response.embeddings[0].values, dtype=np.float32)

	# Retrieve top-K relevant chunks from FAISS index
	def _retrieveChunks(self, queryVector, topK=5) -> list:
		
		# Normalize the query vector and perform the search
		faiss.normalize_L2(queryVector.reshape(1, -1))
		distances, indices = self.wikiEmbedder.index.search(queryVector.reshape(1, -1), topK)
		retrieved = [self.wikiEmbedder.documents[i] for i in indices[0]]
		
		# Return the retrieved chunks
		return retrieved

	# Generate an answer using Gemini with the retrieved chunks as context
	def _generateAnswer(self, question, topChunks) -> str:
		
		# Combine chunks into context and create the prompt
		contextText = "\n".join([f"{chunk['title']}: {chunk['content']}" for chunk in topChunks])
		prompt = f"""
		Use the following wiki content to answer the question:
		\n{contextText}
		\n\nQuestion: {question}
		\nAnswer:"
		"""
		
		# Get the answer using the API
		response = self.client.models.generate_content(
			model="gemini-2.5-flash-lite",
			contents=prompt
		)
		
		# Return the generated answer text
		return response.text