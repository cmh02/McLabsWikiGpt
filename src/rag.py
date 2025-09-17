'''
MCLabs Wiki RAG - RAG Prompting and Response

Author: Chris Hinkson @cmh02
'''

'''
MODULE IMPORTS
'''

# System
import os

# Vector Database
import faiss

# Data Handling
import numpy as np

# Google API
from google import genai

# MCL Packages
from src.docfetch import MCL_WikiEmbedder

'''
RAG CLASS

This class will handle actually performing RAG prompting and response generation.
'''

class MCL_WikiRag():

	# Class Constructor
	def __init__(self, client: genai.Client=None, wikiEmbedder: MCL_WikiEmbedder=None):

		# Make client if not provided
		if client is None:
			self.client = genai.Client(api_key=os.getenv('GOOGLE_GEMINI_API_KEY'))
		else:
			self.client = client

		# Make WikiEmbedder instance if not provided
		if wikiEmbedder is None:
			self.wikiEmbedder = MCL_WikiEmbedder(client=self.client)
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
		You are a helpful assistant for players on a minecraft server. Use the following wiki and Q&A content to answer the given question. Do not hallucinate, and if you don't know the answer, just say you don't know. Be concise but complete.
		\n\nContext: {contextText}
		\n\nQuestion: {question}
		\n\nAnswer:"
		"""
		
		# Get the answer using the API
		response = self.client.models.generate_content(
			model="gemini-2.5-flash-lite",
			contents=prompt
		)
		
		# Return the generated answer text
		return response.text