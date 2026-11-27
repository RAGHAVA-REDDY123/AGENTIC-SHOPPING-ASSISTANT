export interface ProductItem {
  id: number;
  name: string;
  slug?: string;
  brand?: string;
  category_slug?: string;
  price: number;
  original_price?: number;
  discount_percent?: number;
  rating?: number;
  review_count?: number;
  in_stock: boolean;
  stock_quantity?: number;
  features?: Record<string, string>;
  specifications?: Record<string, string>;
}

export interface CartItem {
  id: number;
  product_id: number;
  name: string;
  brand?: string;
  unit_price: number;
  quantity: number;
  subtotal: number;
  image_url?: string;
}

export interface CartData {
  id?: number;
  customer_id?: string;
  total_items: number;
  total_price: number;
  items: CartItem[];
}

export interface ToolChip {
  id: string;
  tool: string;
  label: string;
  status: "running" | "completed";
}

export interface AddressItem {
  id: number;
  title?: string;
  recipient_name: string;
  phone: string;
  address: string;
  is_default?: boolean;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
  products?: ProductItem[];
  addresses?: AddressItem[];
  toolChips?: ToolChip[];
  followups?: string[];
  timestamp: string;
}

export type ConnectionStatus = "connecting" | "connected" | "disconnected";
