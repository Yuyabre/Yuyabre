import { ReactNode } from 'react';
import { TextStreamMessage } from '@/components/ui/Message';

export function useActions() {
  const sendMessage = async (input: string): Promise<ReactNode> => {
    // Simulate AI response delay
    await new Promise((resolve) => setTimeout(resolve, 1000));

    // For now, return a simple text response
    // In the future, this will stream React Server Components
    return (
      <TextStreamMessage
        key={Date.now()}
        content={`I received your message: "${input}". This is a mock response. In the future, I'll be able to help you manage your grocery inventory, place orders, and track expenses!`}
      />
    );
  };

  return { sendMessage };
}

