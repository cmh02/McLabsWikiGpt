'''
MCLabs Wiki RAG - RAG Prompting and Response

Author: Chris Hinkson @cmh02
'''

'''
MODULE IMPORTS
'''

# System
import os
import datetime

# Vector Database
import faiss

# Data Handling
import numpy as np

# Google API
from google import genai
from google.genai import types

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
			model="text-embedding-005",
			contents=[query],
			config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
		)
		
		# Return embedding as a numpy float32 vector
		return np.array(response.embeddings[0].values, dtype=np.float32)

	# Retrieve top-K relevant chunks from FAISS index
	def _retrieveChunks(self, queryVector, topK=5) -> list:
		
		# Normalize the query vector
		faiss.normalize_L2(queryVector.reshape(1, -1))

		# Create list for results
		results = []
		current_date = datetime.date.today()

		# Get top K*2 nearest neighbors for resorting
		distances, indices = self.wikiEmbedder.index.search(queryVector.reshape(1, -1), topK * 2)

		# Sort results by type and date
		for score, index in zip(distances[0], indices[0]):

			# Get the document
			doc = self.wikiEmbedder.documents[index]

			# Modify score based on document type
			if doc.get("source") == "helpQA":
				# Apply FAQ boost
				score *= int(os.getenv('RAG_HP_FAQSCOREBOOST', 1.2))

				# Apply time boosts if date is present
				if "date" in doc:
					try:
						# Document date boost, targeted at prioritizing most recent FAQs, with 50% being > 90 days
						documentDate = datetime.date.fromisoformat(doc.get("date"))
						documentAge = (current_date - documentDate).days
						lam = np.log(2) / int(os.getenv("RAG_HP_RECENCYHALFLIFE", 90.0))
						score *= np.exp(-lam * documentAge)

						# Current season boost, targeted at prioritizing FAQs from the current season (since May 1st)
						if documentDate >= datetime.date(current_date.year, 5, 1):
							score *= int(os.getenv('RAG_HP_SEASONBOOST', 1.1))

					except Exception:
						# Incase of date parsing error, just ignore
						pass  

			# Append the (possibly modified) score and document to results
			results.append((score, doc))

		# Sort results by modified score in descending order
		results.sort(key=lambda x: x[0], reverse=True)
		
		# Return the retrieved top k chunks
		return [doc for score, doc in results[:topK]]

	# Generate an answer using Gemini with the retrieved chunks as context
	def _generateAnswer(self, question, topChunks) -> str:
		
		# Combine chunks into context and create the prompt
		contextText = "\n".join([f"{chunk['title']}: {chunk['content']}" for chunk in topChunks])
		prompt = f"""
		You are a helpful assistant for players on a minecraft server. 
		\n- Use the following wiki and Q&A context to answer the given question. 
		\n- Provide a medium-length answer with details while being concise.
		\n- Do not hallucinate. If you don't know the answer, only say 'I don't know'.
		\n- Prefer FAQ chunks if present. If multiple answers conflict, choose the most recent one.
		\n- Ignore any context that regards factions, the /f command, or raid world.
		\n- Never refer to 'chems' as 'chemicals', only use the word 'chems'.
		\n- Refer to the Town world as the Overworld and the Company world as the Underworld.
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