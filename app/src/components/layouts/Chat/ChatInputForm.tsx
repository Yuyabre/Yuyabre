import type React from "react";
import { ChatInput } from "@/components/layouts/Chat/ChatInput";

interface ChatInputFormProps {
  inputValue: string;
  onInputChange: (value: string) => void;
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
  inputRef: React.RefObject<HTMLInputElement>;
}

export function ChatInputForm({
  inputValue,
  onInputChange,
  onSubmit,
  inputRef,
}: ChatInputFormProps) {
  return (
    <form
      className="flex flex-col gap-2 items-center fixed bottom-0 w-full h-16 bg-background"
      onSubmit={onSubmit}
    >
      <ChatInput ref={inputRef} value={inputValue} onChange={onInputChange} />
    </form>
  );
}
