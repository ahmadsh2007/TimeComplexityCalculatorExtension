import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI()

# Allow connections from anywhere (important for VS Code extensions)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure AI with the API Key from Environment Variables
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

class CodeInput(BaseModel):
    code: str

@app.get("/")
def health():
    return {"status": "running"}

@app.post("/analyze")
def analyze_code(payload: CodeInput):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Strict prompt to ensure clean output
        prompt = f"""
        You are an expert algorithm analyst. 
        Analyze the Time and Space complexity of the following C++ code.
        
        Return ONLY a JSON object in this exact format, with no markdown formatting:
        {{
            "time_complexity": "O(...)",
            "space_complexity": "O(...)",
            "explanation": "One sentence reason."
        }}

        Code:
        {payload.code}
        """
        
        response = model.generate_content(prompt)
        # Clean up if AI adds markdown backticks
        text_response = response.text.replace("```json", "").replace("```", "").strip()
        
        return {"raw_output": text_response}
    except Exception as e:
        # Fallback if something breaks
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="AI Analysis Failed")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)