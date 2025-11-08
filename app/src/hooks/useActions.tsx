import { chatApi } from '@/lib/api';

export function useActions() {
  const sendMessage = async (input: string): Promise<void> => {
    // Only send the message to the API
    // Responses will come through WebSocket
    await chatApi.sendMessage(input);
    
    // Mock: Simulate WebSocket response for demo purposes
    // In production, this would be handled by the WebSocket provider
    setTimeout(() => {
      const mockReceive = (window as any).__mockWebSocketReceive;
      if (mockReceive) {
        const lowerInput = input.toLowerCase();
        if (lowerInput.includes('order') || lowerInput.includes('thuisbezorgd') || lowerInput.includes('deliveroo')) {
          // Simulate order message via WebSocket
          mockReceive({
            type: "message",
            data: {
              message: {
                id: Date.now().toString(),
                role: "assistant",
                type: "order",
                content: "I've prepared an order for you. Please review and approve:",
                orderData: {
                  id: `order-${Date.now()}`,
                  service: "Thuisbezorgd",
                  store: "Albert Heijn",
                  items: [
                    { name: "Milk", quantity: 2, price: 1.75 },
                    { name: "Eggs", quantity: 12, price: 3.50 },
                    { name: "Bread", quantity: 1, price: 2.20 },
                    { name: "Tomatoes", quantity: 500, price: 2.50 },
                  ],
                  subtotal: 9.95,
                  deliveryFee: 2.50,
                  serviceFee: 1.50,
                  total: 13.95,
                  estimatedDeliveryTime: "30-45 min",
                  status: "pending",
                },
              },
            },
          });
        } else {
          // Simulate text message via WebSocket
          mockReceive({
            type: "message",
            data: {
              message: {
                id: Date.now().toString(),
                role: "assistant",
                type: "text",
                content: `I received your message: "${input}". This is a mock response. In the future, I'll be able to help you manage your grocery inventory, place orders, and track expenses!`,
              },
            },
          });
        }
      }
    }, 1000);
  };

  return { sendMessage };
}

