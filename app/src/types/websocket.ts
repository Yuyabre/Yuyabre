import type { IMessage } from "./chat";
import type { Order } from "./orders";

export type WebSocketMessageType =
  | "message"
  | "message_stream"
  | "order_status_update"
  | "order_created"
  | "error";

export interface WebSocketMessage {
  type: WebSocketMessageType;
  data: any;
}

export interface MessageWebSocketData {
  message: IMessage;
}

export interface MessageStreamWebSocketData {
  chunk: string;
  messageId: string;
  done: boolean;
}

export interface OrderStatusUpdateWebSocketData {
  orderId: string;
  status: Order["status"];
}

export interface OrderCreatedWebSocketData {
  order: Order;
}

export interface ErrorWebSocketData {
  error: string;
  code?: string;
}

