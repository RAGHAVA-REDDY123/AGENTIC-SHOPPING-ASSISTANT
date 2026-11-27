import json
import logging
import os
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langchain_core.messages import HumanMessage

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from backend.database.connection import get_db_session, check_db_connection
from backend.graph.workflow import shopping_workflow
from backend.services.cart_service import CartService
from backend.services.product_service import ProductService

# Setup logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("shopping_server")

app = FastAPI(
    title="Nova AI Shopping Assistant - Production API",
    description="Enterprise AI Shopping Concierge with WebSocket Token Streaming and LangGraph Agentic Workflows",
    version="2.0.0",
)

# Enable CORS for Next.js frontend (http://localhost:3000) and any other client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def decimal_serializer(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


def get_cart_dict(customer_id: Optional[str] = None) -> Dict[str, Any]:
    cid = customer_id or os.getenv("DEV_CUSTOMER_ID", "dev_customer_003")
    try:
        with get_db_session() as db:
            cart = CartService(db).get_cart(cid)
            items = []
            for item in cart.items:
                items.append({
                    "id": item.id,
                    "product_id": item.product_id,
                    "name": item.product_name,
                    "brand": item.brand,
                    "unit_price": float(item.unit_price),
                    "quantity": item.quantity,
                    "subtotal": float(item.subtotal),
                    "image_url": item.image_url,
                })
            return {
                "id": cart.id,
                "customer_id": cart.customer_id,
                "total_items": cart.total_items,
                "total_price": float(cart.total_price),
                "items": items,
            }
    except Exception as e:
        logger.error(f"Error fetching cart: {e}")
        return {"items": [], "total_items": 0, "total_price": 0.0}


# =====================================================================
# REST Endpoints
# =====================================================================

@app.get("/api/health")
async def health_check():
    db_status = check_db_connection()
    return {
        "status": "online",
        "service": "AI-Shopping-Assistant",
        "model": os.getenv("GROQ_MODEL_NAME", "openai/gpt-oss-120b"),
        "database": db_status.get("status", "unknown"),
        "customer_id": os.getenv("DEV_CUSTOMER_ID", "dev_customer_003"),
    }


@app.get("/api/cart")
async def get_cart(customer_id: Optional[str] = None):
    return get_cart_dict(customer_id)


@app.get("/api/products/featured")
async def get_featured_products(limit: int = 12):
    try:
        with get_db_session() as db:
            service = ProductService(db)
            products = service.search_products(limit=limit, apply_ranking=True)
            return {"products": products}
    except Exception as e:
        logger.error(f"Error fetching featured products: {e}")
        return {"products": []}


# =====================================================================
# WebSocket Connection Manager & Streamer
# =====================================================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket client connected: session_id={session_id}")

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket client disconnected: session_id={session_id}")

    async def send_json(self, session_id: str, data: Dict[str, Any]):
        ws = self.active_connections.get(session_id)
        if ws:
            try:
                await ws.send_text(json.dumps(data, default=decimal_serializer))
            except Exception as e:
                logger.error(f"Error sending message to {session_id}: {e}")


manager = ConnectionManager()


@app.websocket("/ws/chat/{session_id}")
async def websocket_chat_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(session_id, websocket)

    customer_id = os.getenv("DEV_CUSTOMER_ID", "dev_customer_003")

    # Send initial connection acknowledgment & live cart
    await manager.send_json(session_id, {
        "type": "connected",
        "session_id": session_id,
        "customer_id": customer_id,
        "message": "Connected to Nova Shopping Concierge.",
    })
    initial_cart = get_cart_dict(customer_id)
    await manager.send_json(session_id, {
        "type": "cart_update",
        "cart": initial_cart,
    })

    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                payload = json.loads(raw_data)
            except Exception:
                payload = {"type": "message", "content": raw_data}

            msg_type = payload.get("type", "message")

            # -------------------------------------------------------------
            # Handle Ping
            # -------------------------------------------------------------
            if msg_type == "ping":
                await manager.send_json(session_id, {"type": "pong"})
                continue

            # -------------------------------------------------------------
            # Handle Direct Cart Action (e.g. user clicked "Add to Cart" button)
            # -------------------------------------------------------------
            if msg_type == "action" and payload.get("action") == "add_to_cart":
                product_id = payload.get("product_id")
                quantity = payload.get("quantity", 1)
                try:
                    with get_db_session() as db:
                        res = CartService(db).add_to_cart(product_id=product_id, quantity=quantity, customer_id=customer_id)
                        cart_data = get_cart_dict(customer_id)
                        await manager.send_json(session_id, {
                            "type": "cart_update",
                            "cart": cart_data,
                            "toast": f"Added {quantity} unit(s) to cart!",
                        })
                except Exception as e:
                    await manager.send_json(session_id, {"type": "error", "message": str(e)})
                continue

            # -------------------------------------------------------------
            # Handle Clear Conversation
            # -------------------------------------------------------------
            if msg_type == "clear":
                await manager.send_json(session_id, {
                    "type": "cleared",
                    "message": "Conversation history cleared.",
                })
                continue

            # -------------------------------------------------------------
            # Handle User Chat Message with Token Streaming
            # -------------------------------------------------------------
            if msg_type == "message":
                user_text = payload.get("content", "").strip()
                if not user_text:
                    continue

                logger.info(f"[{session_id}] User: {user_text}")

                # Send initial status indicator
                await manager.send_json(session_id, {
                    "type": "status",
                    "status": "guardrail_check",
                    "label": "Verifying input safety...",
                })

                inputs = {"messages": [HumanMessage(content=user_text)]}
                config = {"configurable": {"thread_id": session_id}}

                accumulated_tokens = []
                extracted_products = []
                extracted_addresses = []

                try:
                    async for event in shopping_workflow.astream_events(inputs, config=config, version="v2"):
                        event_type = event.get("event")
                        event_name = event.get("name", "")
                        data = event.get("data", {})

                        # 1. Pipeline status transitions
                        if event_type == "on_chain_start":
                            if "input_guardrail" in event_name:
                                await manager.send_json(session_id, {
                                    "type": "status",
                                    "status": "guardrail",
                                    "label": "Checking guardrails...",
                                })
                            elif "shopping_agent" in event_name:
                                await manager.send_json(session_id, {
                                    "type": "status",
                                    "status": "thinking",
                                    "label": "Nova is thinking...",
                                })
                            elif "comparison_pipeline" in event_name:
                                await manager.send_json(session_id, {
                                    "type": "status",
                                    "status": "comparing",
                                    "label": "Analyzing side-by-side comparison...",
                                })

                        # 2. Tool Executions & Status Updates
                        elif event_type == "on_tool_start":
                            tool_name = event_name
                            tool_args = data.get("input", {})

                            friendly_labels = {
                                "search_products": f"Searching catalog for '{tool_args.get('query', '')}'",
                                "get_product_details": f"Retrieving specs for '{tool_args.get('identifier', '')}'",
                                "check_inventory": f"Verifying warehouse stock for product #{tool_args.get('product_id', '')}",
                                "add_to_cart": f"Adding product #{tool_args.get('product_id', '')} to cart",
                                "view_cart": "Fetching current shopping cart",
                                "get_saved_addresses": "Retrieving saved delivery addresses",
                                "add_saved_address": "Saving new delivery address",
                                "checkout_cart": "Processing order checkout",
                                "track_order": f"Tracking order #{tool_args.get('order_number', '')}",
                                "get_order_history": "Fetching customer order history",
                                "cancel_order": f"Cancelling order #{tool_args.get('order_number', '')}",
                            }

                            label = friendly_labels.get(tool_name, f"Executing {tool_name}")
                            await manager.send_json(session_id, {
                                "type": "tool_start",
                                "tool": tool_name,
                                "label": label,
                                "args": tool_args,
                            })

                        # 3. Tool Completion & Structured Data Extraction
                        elif event_type == "on_tool_end":
                            tool_name = event_name
                            output = data.get("output", "")

                            # If saved addresses retrieved, extract for interactive address cards
                            if tool_name in ("get_saved_addresses", "add_saved_address"):
                                try:
                                    raw_text = getattr(output, "content", output)
                                    parsed = json.loads(raw_text)
                                    if isinstance(parsed, list) and len(parsed) > 0:
                                        extracted_addresses = parsed
                                        await manager.send_json(session_id, {
                                            "type": "addresses_found",
                                            "addresses": extracted_addresses,
                                        })
                                    elif isinstance(parsed, dict) and "saved_addresses" in parsed:
                                        extracted_addresses = parsed["saved_addresses"]
                                        await manager.send_json(session_id, {
                                            "type": "addresses_found",
                                            "addresses": extracted_addresses,
                                        })
                                except Exception:
                                    pass

                            # If cart was modified, send live cart update
                            if tool_name in ("add_to_cart", "remove_from_cart", "checkout_cart"):
                                fresh_cart = get_cart_dict(customer_id)
                                await manager.send_json(session_id, {
                                    "type": "cart_update",
                                    "cart": fresh_cart,
                                })

                            await manager.send_json(session_id, {
                                "type": "tool_end",
                                "tool": tool_name,
                            })

                        # 4. Token Streaming Chunk (Real-time LLM Output)
                        elif event_type == "on_chat_model_stream":
                            # Only stream tokens generated by the shopping_agent node
                            node_origin = event.get("metadata", {}).get("langgraph_node")
                            if node_origin and node_origin != "shopping_agent":
                                continue

                            chunk = data.get("chunk")
                            if chunk and hasattr(chunk, "content") and chunk.content:
                                text_chunk = str(chunk.content)
                                accumulated_tokens.append(text_chunk)
                                await manager.send_json(session_id, {
                                    "type": "token",
                                    "content": text_chunk,
                                })

                    # Final message closure
                    full_message = "".join(accumulated_tokens)

                    # If no tokens were streamed (e.g. guardrail blocked or comparison pipeline executed)
                    if not full_message.strip():
                        try:
                            state = shopping_workflow.get_state(config)
                            if state and state.values:
                                msgs = state.values.get("messages", [])
                                if msgs:
                                    last_msg = msgs[-1]
                                    full_message = str(getattr(last_msg, "content", ""))
                        except Exception:
                            pass

                    await manager.send_json(session_id, {
                        "type": "message_end",
                        "full_content": full_message,
                        "products": extracted_products,
                        "addresses": extracted_addresses,
                    })

                except Exception as e:
                    logger.error(f"Error during stream execution: {e}", exc_info=True)
                    await manager.send_json(session_id, {
                        "type": "error",
                        "message": f"An error occurred while generating response: {str(e)}",
                    })

    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error for {session_id}: {e}")
        manager.disconnect(session_id)
