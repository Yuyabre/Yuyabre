import { forwardRef } from "react";
import { Label } from "../../ui/label";

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
          className={`bg-muted rounded-md px-2 py-1.5 w-full outline-none text-foreground md:max-w-[500px] max-w-[calc(100dvw-32px)] border border-border focus:ring-2 focus:ring-ring ${
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
