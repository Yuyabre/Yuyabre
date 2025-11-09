import { cloneElement, isValidElement } from "react";
import type React from "react";
import { Message } from "@/components/basic/Message";
import { ChatEmptyState } from "./ChatEmptyState";
import { cn } from "@/lib/utils";

interface ChatMessagesProps {
  messageNodes: React.ReactElement[];
  messagesContainerRef: React.RefObject<HTMLDivElement>;
  messagesEndRef: React.RefObject<HTMLDivElement>;
  onOrderApproved: (approvalMessage: string) => void;
  onSuggestedAction?: (prompt: string) => void;
}

export function ChatMessages({
  messageNodes,
  messagesContainerRef,
  messagesEndRef,
  onOrderApproved,
  onSuggestedAction,
}: ChatMessagesProps) {
  const isEmpty = messageNodes.length === 0;

  return (
    <div
      ref={messagesContainerRef}
      className={cn(
        "flex flex-col gap-3 h-full w-dvw items-center overflow-y-scroll px-4 md:px-0",
        isEmpty ? "justify-center" : "justify-start py-6"
      )}
    >
      {isEmpty ? (
        <ChatEmptyState onSuggestedAction={onSuggestedAction} />
      ) : (
        <>
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
        </>
      )}
    </div>
  );
}

