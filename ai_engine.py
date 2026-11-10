import os
import json
import time
from pathlib import Path
from google import genai
from google.genai import types
from PIL import Image
from dotenv import load_dotenv

# Ensure .env is read from the exact file directory
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError(f"GEMINI_API_KEY not found in {env_path}")

client = genai.Client(api_key=api_key)

# Fallback sequence to prevent 404/503 errors during spikes
CANDIDATE_MODELS = [
    "models/gemini-3.1-flash-lite",
    "models/gemini-2.5-flash",
    "models/gemini-3.5-flash-lite",
]

SYSTEM_INSTRUCTION = """
You are the PayPal Dispute Copilot backend engine.
Your job is to analyze user-submitted claim text and an uploaded evidence image.

Evaluate the case against PayPal Buyer Protection standards:
1. "Item Not Received" (INR): Needs proof of purchase, tracking details, delivery SLA breach.
2. "Significantly Not As Described" (SNAD): Material damage, wrong item, counterfeit, missing major parts. Requires physical visual proof.

Rules for your output:
- If a user claims physical damage (SNAD) but provides NO image, set `is_complete` to false and specify the missing photo in `missing_evidence`.
- If an image is provided, inspect the image to see if it shows verifiable damage, packaging slips, or receipts.
- Construct a chronological timeline of 3-4 steps based on dates mentioned or realistic dispute progression.
- Provide a clear recommendation (e.g., ISSUE_FULL_REFUND, PARTIAL_REFUND_OFFER, REQUEST_INFO) along with a confidence score (0-100) and rationale.
"""

JSON_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "claim_type": {"type": "STRING"},
        "missing_evidence": {"type": "ARRAY", "items": {"type": "STRING"}},
        "is_complete": {"type": "BOOLEAN"},
        "timeline": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {"date": {"type": "STRING"}, "event": {"type": "STRING"}},
                "required": ["date", "event"],
            },
        },
        "agent_dossier": {
            "type": "OBJECT",
            "properties": {
                "summary": {"type": "STRING"},
                "policy_fit": {"type": "STRING"},
                "recommended_action": {"type": "STRING"},
                "confidence_score": {"type": "INTEGER"},
                "rationale": {"type": "STRING"},
            },
            "required": [
                "summary",
                "policy_fit",
                "recommended_action",
                "confidence_score",
                "rationale",
            ],
        },
    },
    "required": [
        "claim_type",
        "missing_evidence",
        "is_complete",
        "timeline",
        "agent_dossier",
    ],
}


def analyze_dispute(claim_text: str, image_file=None) -> dict:
    """
    Analyzes dispute with automated model fallback and retry logic.
    """
    contents = [f"Buyer's Claim Description:\n{claim_text}"]

    if image_file is not None:
        try:
            image = Image.open(image_file)
            contents.append(image)
        except Exception as e:
            return {"error": f"Failed to process image: {str(e)}"}

    last_error = None

    for model_name in CANDIDATE_MODELS:
        for _ in range(2):  # Retry each model up to twice if busy
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        response_mime_type="application/json",
                        response_schema=JSON_SCHEMA,
                        temperature=0.2,
                    ),
                )
                return json.loads(response.text)
            except Exception as e:
                last_error = e
                err_str = str(e)
                if "503" in err_str:
                    time.sleep(1)
                    continue
                elif "404" in err_str:
                    break
                else:
                    break

    return {
        "error": str(last_error),
        "claim_type": "Evaluation Error",
        "is_complete": False,
        "missing_evidence": [f"API Connection Error: {str(last_error)}"],
        "timeline": [],
        "agent_dossier": {
            "summary": "Service temporarily unreachable.",
            "policy_fit": "N/A",
            "recommended_action": "REQUEST_INFO",
            "confidence_score": 0,
            "rationale": "Model invocation failed across candidate endpoints.",
        },
    }


if __name__ == "__main__":
    print("Testing ai_engine.py locally...")
    sample_text = "I ordered a wireless headphone for $120. When it arrived, the package was torn and the left earcup was snapped in half. Seller won't reply."
    result = analyze_dispute(sample_text)
    print("\nResult:")
    print(json.dumps(result, indent=2))
