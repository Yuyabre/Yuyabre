import { cloneElement, isValidElement } from "react";
import type React from "react";
import { Message } from "@/components/basic/Message";

interface ChatMessagesProps {
  messageNodes: React.ReactElement[];
  messagesContainerRef: React.RefObject<HTMLDivElement>;
  messagesEndRef: React.RefObject<HTMLDivElement>;
  onOrderApproved: (approvalMessage: string) => void;
}

export function ChatMessages({
  messageNodes,
  messagesContainerRef,
  messagesEndRef,
  onOrderApproved,
}: ChatMessagesProps) {
  return (
    <div
      ref={messagesContainerRef}
      className="flex flex-col gap-3 h-full w-dvw items-center overflow-y-scroll"
    >
      {messageNodes.map((message, index) => {
        if (isValidElement(message) && message.type === Message) {
          return cloneElement(
            message as React.ReactElement<
              React.ComponentProps<typeof Message>
            >,
            {
              key: message.key || index,
              onOrderApproved,
            }
          );
        }
        return message;
      })}
      <div ref={messagesEndRef} />
    </div>
  );
}

