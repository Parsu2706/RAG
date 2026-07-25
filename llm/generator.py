from google import genai
import os 
from dotenv import load_dotenv
load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
model = "gemini-2.5-flash-lite"

def generate_response(prompt): 
    try: 
        response = client.models.generate_content(
            model = model , contents=prompt
        )
        return response.text
    except Exception as e : 
        return f"Error generating response: {e}"