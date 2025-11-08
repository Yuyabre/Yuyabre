import { Button as RadixButton } from "@radix-ui/themes";
import { ReactNode } from "react";
import clsx from "clsx";

interface ButtonProps {
  children: ReactNode;
  onClick?: () => void;
  variant?: "solid" | "soft" | "outline" | "ghost";
  size?: "1" | "2" | "3" | "4";
  className?: string;
  asChild?: boolean;
  disabled?: boolean;
  "aria-label"?: string;
}

export function Button({
  children,
  onClick,
  variant = "ghost",
  size = "2",
  className,
  asChild,
  disabled,
  "aria-label": ariaLabel,
}: ButtonProps) {
  // Use style prop to override colors for monochrome theme when needed
  // This leverages Radix's token system as recommended in their docs
  const getButtonStyle = () => {
    if (variant === "solid") {
      return {
        backgroundColor: "var(--color-bg-inverse)",
        color: "var(--color-text-inverse)",
      };
    }
    return undefined;
  };

  return (
    <RadixButton
      variant={variant}
      size={size}
      onClick={onClick}
      className={clsx(className)}
      style={getButtonStyle()}
      asChild={asChild}
      disabled={disabled}
      aria-label={ariaLabel}
    >
      {children}
    </RadixButton>
  );
}
