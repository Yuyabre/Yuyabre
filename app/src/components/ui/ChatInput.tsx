import { forwardRef } from "react";
import { Label } from "./Label";

interface ChatInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "onChange"> {
  value: string;
  onChange: (value: string) => void;
}

export const ChatInput = forwardRef<HTMLInputElement, ChatInputProps>(
  ({ value, onChange, className, id = "chat-input", ...props }, ref) => {
    return (
      <>
        <Label htmlFor={id} className="sr-only">
          Send a message
        </Label>
        <input
          ref={ref}
          id={id}
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className={`bg-theme-tertiary rounded-md px-2 py-1.5 w-full outline-none text-theme-primary md:max-w-[500px] max-w-[calc(100dvw-32px)] border border-theme-primary focus:ring-2 focus:ring-accent ${
            className || ""
          }`}
          placeholder="Send a message..."
          {...props}
        />
      </>
    );
  }
);

ChatInput.displayName = "ChatInput";
