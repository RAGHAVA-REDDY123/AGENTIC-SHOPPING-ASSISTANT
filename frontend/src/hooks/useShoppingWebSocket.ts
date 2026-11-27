"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { ChatMessage, ConnectionStatus, CartData, ProductItem, ToolChip, AddressItem } from "@/types/chat";

export function useShoppingWebSocket() {
  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [cart, setCart] = useState<CartData>({ total_items: 0, total_price: 0, items: [] });
  const [liveActivity, setLiveActivity] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);

  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef<number>(0);
  const sessionIdRef = useRef<string>("");

  // Initialize Session ID
  useEffect(() => {
    let sid = typeof window !== "undefined" ? sessionStorage.getItem("nova_session_id") : null;
    if (!sid) {
      sid = "nova-" + Math.random().toString(36).substring(2, 10);
      if (typeof window !== "undefined") {
        sessionStorage.setItem("nova_session_id", sid);
      }
    }
    sessionIdRef.current = sid;
  }, []);

  // Show temporary toast
  const triggerToast = useCallback((message: string, type: "success" | "error" = "success") => {
    setToast({ message, type });
    setTimeout(() => {
      setToast((prev) => (prev?.message === message ? null : prev));
    }, 3500);
  }, []);

  // WebSocket connection logic
  const connect = useCallback(() => {
    if (typeof window === "undefined") return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    // Default to localhost:8000 where FastAPI backend runs
    const defaultHost = "localhost:8000";
    const wsBase = process.env.NEXT_PUBLIC_WS_URL || `${protocol}//${defaultHost}`;
    const wsUrl = `${wsBase}/ws/chat/${sessionIdRef.current || "nova-session"}`;

    setStatus("connecting");

    try {
      const ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onopen = () => {
        reconnectAttemptsRef.current = 0;
        setStatus("connected");
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleServerEvent(data);
        } catch (err) {
          console.error("Error parsing WebSocket event:", err);
        }
      };

      ws.onclose = () => {
        setStatus("disconnected");
        scheduleReconnect();
      };

      ws.onerror = (err) => {
        console.error("WebSocket connection error:", err);
        ws.close();
      };
    } catch (e) {
      console.error("Failed to construct WebSocket:", e);
      scheduleReconnect();
    }
  }, []);

  const scheduleReconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) return;
    const delay = Math.min(1000 * Math.pow(1.5, reconnectAttemptsRef.current), 10000);
    reconnectAttemptsRef.current += 1;
    reconnectTimeoutRef.current = setTimeout(() => {
      reconnectTimeoutRef.current = null;
      connect();
    }, delay);
  }, [connect]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [connect]);

  // Handle Inbound Server Events
  const handleServerEvent = useCallback((data: any) => {
    switch (data.type) {
      case "connected":
        break;

      case "status":
        setLiveActivity(data.label || "Nova is processing...");
        break;

      case "tool_start":
        setLiveActivity(data.label || `Calling ${data.tool}...`);
        setMessages((prev) => {
          if (!prev.length) return prev;
          const updated = [...prev];
          const lastIndex = updated.length - 1;
          const lastMsg = { ...updated[lastIndex] };

          if (lastMsg.role === "assistant") {
            const currentChips = lastMsg.toolChips ? [...lastMsg.toolChips] : [];
            const newChip: ToolChip = {
              id: "tool-" + Date.now(),
              tool: data.tool,
              label: data.label || `Calling ${data.tool}...`,
              status: "running",
            };
            lastMsg.toolChips = [...currentChips, newChip];
            updated[lastIndex] = lastMsg;
          }
          return updated;
        });
        break;

      case "tool_end":
        setLiveActivity(null);
        setMessages((prev) => {
          if (!prev.length) return prev;
          const updated = [...prev];
          const lastIndex = updated.length - 1;
          const lastMsg = { ...updated[lastIndex] };

          if (lastMsg.role === "assistant" && lastMsg.toolChips?.length) {
            const chips = [...lastMsg.toolChips];
            chips[chips.length - 1] = {
              ...chips[chips.length - 1],
              status: "completed",
            };
            lastMsg.toolChips = chips;
            updated[lastIndex] = lastMsg;
          }
          return updated;
        });
        break;

      case "token":
        setMessages((prev) => {
          if (!prev.length) return prev;
          const updated = [...prev];
          const lastIndex = updated.length - 1;
          const lastMsg = { ...updated[lastIndex] };

          if (lastMsg.role === "assistant") {
            lastMsg.content = (lastMsg.content || "") + (data.content || "");
            lastMsg.isStreaming = true;
            updated[lastIndex] = lastMsg;
          }
          return updated;
        });
        break;

      case "products_found":
        if (data.products && Array.isArray(data.products)) {
          setMessages((prev) => {
            if (!prev.length) return prev;
            const updated = [...prev];
            const lastIndex = updated.length - 1;
            const lastMsg = { ...updated[lastIndex] };

            if (lastMsg.role === "assistant") {
              lastMsg.products = data.products as ProductItem[];
              updated[lastIndex] = lastMsg;
            }
            return updated;
          });
        }
        break;

      case "addresses_found":
        if (data.addresses && Array.isArray(data.addresses)) {
          setMessages((prev) => {
            if (!prev.length) return prev;
            const updated = [...prev];
            const lastIndex = updated.length - 1;
            const lastMsg = { ...updated[lastIndex] };

            if (lastMsg.role === "assistant") {
              lastMsg.addresses = data.addresses as AddressItem[];
              updated[lastIndex] = lastMsg;
            }
            return updated;
          });
        }
        break;

      case "message_end":
        setLiveActivity(null);
        setIsGenerating(false);
        setMessages((prev) => {
          if (!prev.length) return prev;
          const updated = [...prev];
          const lastIndex = updated.length - 1;
          const lastMsg = { ...updated[lastIndex] };

          if (lastMsg.role === "assistant") {
            if (data.full_content) {
              lastMsg.content = data.full_content;
            }
            if (data.addresses && Array.isArray(data.addresses)) {
              lastMsg.addresses = data.addresses as AddressItem[];
            }
            lastMsg.isStreaming = false;
            lastMsg.followups = [
              "What is in my cart?",
              "Proceed to checkout",
              "Track my order",
            ];
            updated[lastIndex] = lastMsg;
          }
          return updated;
        });
        break;

      case "cart_update":
        if (data.cart) {
          setCart(data.cart);
        }
        if (data.toast) {
          triggerToast(data.toast, "success");
        }
        break;

      case "cleared":
        setMessages([]);
        triggerToast("Conversation cleared", "success");
        break;

      case "error":
        setLiveActivity(null);
        setIsGenerating(false);
        triggerToast(data.message || "An error occurred", "error");
        setMessages((prev) => [
          ...prev,
          {
            id: "err-" + Date.now(),
            role: "assistant",
            content: `⚠️ ${data.message || "An unexpected error occurred."}`,
            timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          },
        ]);
        break;
    }
  }, [triggerToast]);

  // Send a user message
  const sendMessage = useCallback((text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      triggerToast("Server disconnected. Reconnecting...", "error");
      return;
    }

    const timestamp = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

    // Append User Message
    const userMsg: ChatMessage = {
      id: "user-" + Date.now(),
      role: "user",
      content: trimmed,
      timestamp,
    };

    // Prepare Assistant Placeholder
    const aiMsg: ChatMessage = {
      id: "ai-" + (Date.now() + 1),
      role: "assistant",
      content: "",
      isStreaming: true,
      timestamp,
    };

    setMessages((prev) => [...prev, userMsg, aiMsg]);
    setIsGenerating(true);

    socketRef.current.send(
      JSON.stringify({
        type: "message",
        content: trimmed,
      })
    );
  }, [triggerToast]);

  // Direct Cart Action (Clicking Add to Cart button on a product card)
  const addToCart = useCallback((productId: number, quantity: number = 1) => {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      triggerToast("Server disconnected. Reconnecting...", "error");
      return;
    }

    socketRef.current.send(
      JSON.stringify({
        type: "action",
        action: "add_to_cart",
        product_id: productId,
        quantity,
      })
    );
  }, [triggerToast]);

  // Clear Session
  const clearChat = useCallback(() => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: "clear" }));
    }
    setMessages([]);
    sessionIdRef.current = "nova-" + Math.random().toString(36).substring(2, 10);
    if (typeof window !== "undefined") {
      sessionStorage.setItem("nova_session_id", sessionIdRef.current);
    }
  }, []);

  // Stop Generation
  const stopGeneration = useCallback(() => {
    setIsGenerating(false);
    setLiveActivity(null);
    setMessages((prev) => {
      if (!prev.length) return prev;
      const updated = [...prev];
      const lastIndex = updated.length - 1;
      if (updated[lastIndex].isStreaming) {
        updated[lastIndex] = { ...updated[lastIndex], isStreaming: false };
      }
      return updated;
    });
  }, []);

  return {
    status,
    messages,
    cart,
    liveActivity,
    isGenerating,
    toast,
    sendMessage,
    addToCart,
    clearChat,
    stopGeneration,
  };
}
