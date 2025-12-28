import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from functools import lru_cache 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

class CodeInput(BaseModel):
    code: str
    model: str = "gemini-flash-latest"

@app.get("/")
def health():
    return {"status": "running"}

@lru_cache(maxsize=100)
def get_gemini_response(code_hash: int, code: str, model_name: str):
    try:
        model = genai.GenerativeModel(model_name)
        
        prompt = f"""
        Role: Senior Algorithm Analyst.
        Task: Analyze Time and Space complexity. Determine confidence based on code clarity.

        [EXAMPLES]
        Input: "for(int i=0; i<n; i++) {{ ... }}"
        Output: {{ 
            "time_complexity": "O(N)", 
            "time_confidence": "High",
            "space_complexity": "O(1)", 
            "space_confidence": "High",
            "explanation": "Simple linear loop." 
        }}

        Input: "void complexFunc() {{ /* obscure recursive math with random jumps */ }}"
        Output: {{ 
            "time_complexity": "O(N^2)", 
            "time_confidence": "Low",
            "space_complexity": "O(N)", 
            "space_confidence": "Medium",
            "explanation": "Control flow is ambiguous." 
        }}

        [YOUR TURN]
        Analyze the code. Return ONLY JSON.
        Confidence levels: "High" (Sure), "Medium" (Likely), "Low" (Guess).
        
        {{
            "time_complexity": "O(...)",
            "time_confidence": "...",
            "space_complexity": "O(...)",
            "space_confidence": "...",
            "explanation": "One sentence reason."
        }}

        Code:
        {code}
        """
        
        response = model.generate_content(prompt)
        text_response = response.text.replace("```json", "").replace("```", "").strip()
        return text_response
    except Exception as e:
        print(f"GenAI Error: {e}")
        return None

@app.post("/analyze")
def analyze_code(payload: CodeInput):
    if len(payload.code) > 10000:
        raise HTTPException(status_code=400, detail="Code too long (max 10,000 characters).")

    result = get_gemini_response(hash(payload.code), payload.code, payload.model)
    
    if result is None:
        raise HTTPException(status_code=500, detail="AI Analysis Failed")
        
    return {"raw_output": result}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)