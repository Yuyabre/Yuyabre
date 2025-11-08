import type React from "react";
import { ChatInput } from "@/components/basic/ChatInput";

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
      className="flex flex-col gap-2 relative items-center"
      onSubmit={onSubmit}
    >
      <ChatInput ref={inputRef} value={inputValue} onChange={onInputChange} />
    </form>
  );
}
