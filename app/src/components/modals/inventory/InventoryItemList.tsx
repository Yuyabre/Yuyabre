import type { InventoryItem } from "@/types";
import { InventoryItemCard } from "./InventoryItemCard";
import { Skeleton } from "@/components/ui/skeleton";

interface InventoryItemListProps {
  items: InventoryItem[];
  isLoading?: boolean;
}

export function InventoryItemList({
  items,
  isLoading,
}: InventoryItemListProps) {

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className="rounded-lg border border-border p-4 space-y-3"
          >
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-3 w-48" />
            <Skeleton className="h-3 w-24" />
          </div>
        ))}
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p className="text-sm">
          No inventory items yet. Add your first item to get started!
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <InventoryItemCard key={item.item_id} item={item} />
      ))}
    </div>
  );
}

