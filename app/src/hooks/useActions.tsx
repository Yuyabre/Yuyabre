import { ReactNode } from 'react';
import { Message } from '@/components/ui/Message';
import { MessageRole, MessageType } from '@/types/chat';

export function useActions() {
  const sendMessage = async (input: string): Promise<ReactNode> => {
    // Simulate AI response delay
    await new Promise((resolve) => setTimeout(resolve, 1000));

    // Check if the input is about ordering something
    const lowerInput = input.toLowerCase();
    if (lowerInput.includes('order') || lowerInput.includes('thuisbezorgd') || lowerInput.includes('deliveroo')) {
      // Return an order card message
      return (
        <Message
          key={Date.now()}
          id={Date.now().toString()}
          role={MessageRole.ASSISTANT}
          type={MessageType.ORDER}
          content="I've prepared an order for you. Please review and approve:"
          orderData={{
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
          }}
        />
      );
    }

    // Default text response
    return (
      <Message
        key={Date.now()}
        id={Date.now().toString()}
        role={MessageRole.ASSISTANT}
        type={MessageType.TEXT}
        content={`I received your message: "${input}". This is a mock response. In the future, I'll be able to help you manage your grocery inventory, place orders, and track expenses!`}
      />
    );
  };

  return { sendMessage };
}

