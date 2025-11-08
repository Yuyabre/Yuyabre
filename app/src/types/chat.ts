export enum MessageRole {
  ASSISTANT = "assistant",
  USER = "user",
}

export enum MessageType {
  TEXT = "text",
  ORDER = "order",
}

export interface IMessage {
  id: string;
  role: MessageRole;
  type: MessageType;
  content: string;
  timestamp?: Date;
  orderData?: {
    id: string;
    service: string;
    store: string;
    items: Array<{
      name: string;
      quantity: number;
      price: number;
    }>;
    subtotal: number;
    deliveryFee?: number;
    serviceFee?: number;
    total: number;
    estimatedDeliveryTime: string;
    status: "pending" | "preparing" | "delivering" | "delivered";
  };
}
