'''
MCLabs Wiki GPT

Author: Chris Hinkson @cmh02
'''

'''
MODULE IMPORTS
'''
import os
import faiss
import numpy as np
import dotenv
from google import genai

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
GEMINI TEST RESPONSE
'''

response = client.models.generate_content(
    model="gemini-2.5-flash-lite", 
	contents="Explain how AI works in a few words"
)
print(response.text)

