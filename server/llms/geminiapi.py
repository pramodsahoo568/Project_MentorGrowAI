import google.generativeai as genai
import os
from dotenv import load_dotenv
load_dotenv()
# Configure your API Key (Best practice is using environment variables)
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Define your safety settings (Note: Python uses Enums or strings)
safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    }
]


async def ask_gemini(prompt: str):
    """
    Python equivalent of your Node.js askGemini function.
    """
    '''  for model in genai.list_models():
        print(model.name)
    '''
    try:
        # Initialize the model
        model = genai.GenerativeModel(
            model_name="models/gemini-2.5-flash" # Note: Verify specific 2.5 vs 1.5 naming in your region
        )

        # Generate content (await is used if using an async library,
        # but the standard genai call is synchronous unless using vertexai)
        response = model.generate_content(prompt)

        return response.text

    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return "Error: Could not reach the AI server."