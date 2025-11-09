import { forwardRef } from "react";
import { Label } from "../../ui/label";

interface ChatInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "onChange"> {
  value: string;
  onChange: (value: string) => void;
}

export const ChatInput = forwardRef<HTMLInputElement, ChatInputProps>(
  (
    {
      value,
      onChange,
      className,
      id = "chat-input",
      disabled,
      ...props
    },
    ref
  ) => {
    return (
      <div className="flex-1">
        <Label htmlFor={id} className="sr-only">
          Send a message
        </Label>
        <input
          ref={ref}
          id={id}
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          className={
            "w-full border border-transparent bg-muted/60 px-3 py-2 text-sm text-foreground outline-none transition focus-visible:ring-0 focus-visible:border-primary disabled:cursor-not-allowed disabled:opacity-60" +
            (className ? ` ${className}` : "")
          }
          placeholder="Send a message..."
          {...props}
        />
      </div>
    );
  }
);

ChatInput.displayName = "ChatInput";
