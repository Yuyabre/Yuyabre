import { useState, useRef, ReactNode, cloneElement, isValidElement, useEffect } from "react";
import { motion } from "framer-motion";
import { useScrollToBottom } from "@/hooks/useScrollToBottom";
import { useActions } from "@/hooks/useActions";
import { useWebSocket } from "@/providers/WebSocketProvider";
import { Message } from "@/components/ui/Message";
import { ActionButton } from "@/components/ui/ActionButton";
import { ChatInput } from "@/components/ui/ChatInput";
import { MessageRole, MessageType } from "@/types/chat";

export default function Chat() {
  const { sendMessage } = useActions();
  const { onMessage } = useWebSocket();

  const [input, setInput] = useState<string>("");
  const [messages, setMessages] = useState<Array<ReactNode>>([]);

  const inputRef = useRef<HTMLInputElement>(null);
  const [messagesContainerRef, messagesEndRef] =
    useScrollToBottom<HTMLDivElement>();

  // Listen for incoming messages via WebSocket
  useEffect(() => {
    const unsubscribe = onMessage((message) => {
      setMessages((msgs) => [
        ...msgs,
        <Message
          key={message.id}
          id={message.id}
          role={message.role as MessageRole}
          type={message.type as MessageType}
          content={message.content}
          orderData={message.orderData}
        />,
      ]);
    });

    return unsubscribe;
  }, [onMessage]);

  const suggestedActions = [
    {
      title: "What's in",
      label: "the inventory?",
      action: "What's in the inventory?",
    },
    {
      title: "Order",
      label: "2 liters of milk",
      action: "Order 2 liters of milk",
    },
    {
      title: "Show me",
      label: "pending expenses",
      action: "Show me pending expenses",
    },
    {
      title: "Check",
      label: "low stock items",
      action: "Check low stock items",
    },
  ];

  return (
    <div className="flex flex-row justify-center pb-20 h-dvh bg-white dark:bg-zinc-900">
      <div className="flex flex-col justify-between gap-4">
        <div
          ref={messagesContainerRef}
          className="flex flex-col gap-3 h-full w-dvw items-center overflow-y-scroll"
        >
          {messages.map((message, index) => {
            // If it's a Message component, clone it and add the approval callback
            if (isValidElement(message) && message.type === Message) {
              return cloneElement(message, {
                key: message.key || index,
                onOrderApproved: (approvalMessage: string) => {
                  // Add a follow-up message with the approval response
                  setMessages((msgs) => [
                    ...msgs,
                    <Message
                      key={Date.now()}
                      id={Date.now().toString()}
                      role={MessageRole.ASSISTANT}
                      type={MessageType.TEXT}
                      content={approvalMessage}
                    />,
                  ]);
                },
              });
            }
            return message;
          })}
          <div ref={messagesEndRef} />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full px-4 md:px-0 mx-auto md:max-w-[500px] mb-4">
          {messages.length === 0 &&
            suggestedActions.map((action, index) => (
              <ActionButton
                key={index}
                index={index}
                title={action.title}
                label={action.label}
                onClick={async () => {
                  setMessages((messages) => [
                    ...messages,
                    <Message
                      key={messages.length}
                      id={Date.now().toString()}
                      role={MessageRole.USER}
                      type={MessageType.TEXT}
                      content={action.action}
                    />,
                  ]);
                  // Send message - response will come via WebSocket
                  await sendMessage(action.action);
                }}
              />
            ))}
        </div>

        <form
          className="flex flex-col gap-2 relative items-center"
          onSubmit={async (event) => {
            event.preventDefault();
            if (!input.trim()) return;

            const currentInput = input;
            setMessages((messages) => [
              ...messages,
              <Message
                key={messages.length}
                id={Date.now().toString()}
                role={MessageRole.USER}
                type={MessageType.TEXT}
                content={currentInput}
              />,
            ]);
            setInput("");

            // Send message - response will come via WebSocket
            await sendMessage(currentInput);
          }}
        >
          <ChatInput ref={inputRef} value={input} onChange={setInput} />
        </form>
      </div>
    </div>
  );
}
