import { Separator as RadixSeparator } from "@radix-ui/themes";

interface SeparatorProps {
  orientation?: "horizontal" | "vertical";
  decorative?: boolean;
  className?: string;
}

export function Separator({
  orientation = "horizontal",
  decorative = true,
  className = "",
}: SeparatorProps) {
  // Use Radix UI Themes Separator which handles styling automatically
  // Use border-muted for better visibility (lighter than border-secondary)
  return (
    <RadixSeparator
      decorative={decorative}
      orientation={orientation}
      className={className}
      style={{
        backgroundColor: "var(--color-border-muted)",
        width: orientation === "horizontal" ? "100%" : undefined,
        height: orientation === "vertical" ? "100%" : undefined,
      }}
    />
  );
}
