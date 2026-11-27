import os
import sys
import uvicorn
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

from backend.database.connection import check_db_connection

def main():
    print("=" * 75)
    print("🚀 NOVA AI SHOPPING ASSISTANT - FASTAPI WEBSOCKET SERVER")
    print("=" * 75)

    db_check = check_db_connection()
    if db_check.get("status") == "healthy":
        print(f"  ✅ Database: Connected to PostgreSQL (pgvector healthy)")
    else:
        print(f"  ⚠️  Database warning: {db_check.get('error')}")

    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        masked = groq_key[:8] + "..." + groq_key[-4:]
        print(f"  ✅ Groq API Key: Configured ({masked})")
    else:
        print(f"  ❌ Groq API Key: Missing in .env")

    model = os.getenv("GROQ_MODEL_NAME", "openai/gpt-oss-120b")
    print(f"  ✅ Active Model: {model}")
    print(f"  ✅ WebSocket Endpoint: ws://localhost:8000/ws/chat/<session_id>")
    print(f"  🌐 API Server: http://localhost:8000")
    print("=" * 75)
    print("Starting server on port 8000... Press Ctrl+C to stop.\n")

    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.server:app", host="0.0.0.0", port=port, reload=True)

if __name__ == "__main__":
    main()
