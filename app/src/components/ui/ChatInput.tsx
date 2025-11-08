import { forwardRef } from "react";

interface ChatInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "onChange"> {
  value: string;
  onChange: (value: string) => void;
}

export const ChatInput = forwardRef<HTMLInputElement, ChatInputProps>(
  ({ value, onChange, className, ...props }, ref) => {
    return (
      <input
        ref={ref}
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`bg-zinc-100 dark:bg-zinc-700 rounded-md px-2 py-1.5 w-full outline-none text-zinc-800 dark:text-zinc-300 md:max-w-[500px] max-w-[calc(100dvw-32px)] border border-zinc-200 dark:border-zinc-800 ${
          className || ""
        }`}
        placeholder="Send a message..."
        {...props}
      />
    );
  }
);

ChatInput.displayName = "ChatInput";
