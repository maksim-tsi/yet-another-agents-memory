import os

from google import genai

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not set")

client = genai.Client(api_key=GOOGLE_API_KEY)

response = client.models.generate_content(model="gemini-2.5-flash-lite", contents="tell me a joke")
print(response.text)
