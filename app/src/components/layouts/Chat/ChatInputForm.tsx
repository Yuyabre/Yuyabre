import type React from "react";
import { ChatInput } from "@/components/layouts/Chat/ChatInput";
import { IconLoader2, IconMessageDots, IconSend } from "@tabler/icons-react";

interface ChatInputFormProps {
  inputValue: string;
  onInputChange: (value: string) => void;
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
  inputRef: React.RefObject<HTMLInputElement>;
  isStreaming: boolean;
}

export function ChatInputForm({
  inputValue,
  onInputChange,
  onSubmit,
  inputRef,
  isStreaming,
}: ChatInputFormProps) {
  const isEmpty = !inputValue.trim();

  return (
    <form
      className="fixed bottom-0 left-0 right-0 flex justify-center bg-gradient-to-t from-background via-background/95 to-background/60 pb-4 pt-3"
      onSubmit={onSubmit}
    >
      <div className="flex w-full max-w-3xl items-end gap-2 px-4">
        <div className="flex w-full flex-col gap-2 rounded-2xl border border-border/70 bg-card/90 p-2 shadow-lg shadow-black/5">
          <div className="flex items-center justify-between px-2 text-xs text-muted-foreground">
            <div className="inline-flex items-center gap-1">
              <IconMessageDots className="size-3.5" />
              <span>
                {isStreaming ? "Assistant is responding..." : "Ready for your next question"}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2 px-2">
            <ChatInput
              ref={inputRef}
              value={inputValue}
              onChange={onInputChange}
              disabled={isStreaming}
              className="border-0 bg-transparent px-0 py-0 text-base"
            />
            <button
              type="submit"
              className="inline-flex size-11 items-center justify-center rounded-full bg-primary text-primary-foreground transition disabled:cursor-not-allowed disabled:bg-muted disabled:text-muted-foreground"
              disabled={isStreaming || isEmpty}
              aria-label={isStreaming ? "Assistant is responding" : "Send message"}
            >
              {isStreaming ? (
                <IconLoader2 className="size-5 animate-spin" />
              ) : (
                <IconSend className="size-5" />
              )}
            </button>
          </div>
        </div>
      </div>
    </form>
  );
}
