import { ActionButton } from "@/components/basic/ActionButton";

const SUGGESTED_ACTIONS = [
  {
    title: "What's in",
    label: "the inventory?",
    action: "What's in the inventory?",
  },
  {
    title: "Order",
    label: "2 liters of milk",
    action: "Order 2 liters of milk",
  },
  {
    title: "Show me",
    label: "pending expenses",
    action: "Show me pending expenses",
  },
  {
    title: "Check",
    label: "low stock items",
    action: "Check low stock items",
  },
];

interface ChatSuggestedActionsProps {
  visible: boolean;
  onSelect: (action: string) => void;
}

export function ChatSuggestedActions({
  visible,
  onSelect,
}: ChatSuggestedActionsProps) {
  if (!visible) {
    return null;
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full px-4 md:px-0 mx-auto md:max-w-[500px] mb-4">
      {SUGGESTED_ACTIONS.map((suggestion, index) => (
        <ActionButton
          key={index}
          index={index}
          title={suggestion.title}
          label={suggestion.label}
          onClick={() => onSelect(suggestion.action)}
        />
      ))}
    </div>
  );
}

