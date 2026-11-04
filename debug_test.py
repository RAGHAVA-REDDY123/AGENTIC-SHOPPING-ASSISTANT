import sys
import time
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

print("Importing shopping_workflow...")
from backend.graph.workflow import shopping_workflow
from langchain_core.messages import HumanMessage

print("Invoking workflow with comparison...")
start = time.time()
try:
    ans = shopping_workflow.invoke(
        {"messages": [HumanMessage(content="compare ASUS ROG Strix G15 Gaming Laptop vs Apple MacBook Pro 14 M3")]},
        config={"configurable": {"thread_id": "test_debug_99"}}
    )
    duration = time.time() - start
    print(f"Workflow completed in {duration:.2f}s!")
    print(f"Total messages in state: {len(ans.get('messages', []))}")
    for i, m in enumerate(ans.get("messages", [])):
        print(f"[{i}] {getattr(m, 'type', 'unknown')}: {m.content[:80]}...")
except Exception as e:
    print(f"Error after {time.time() - start:.2f}s: {type(e).__name__}: {e}")

