import { useState } from "react";
import { toast } from "sonner";
import type { InventoryItem } from "@/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  IconEdit,
  IconTrash,
  IconCheck,
  IconX,
  IconAlertTriangle,
} from "@tabler/icons-react";
import { useUpdateInventoryItem, useDeleteInventoryItem } from "@/lib/queries";
import { cn } from "@/lib/utils";
import { useStore } from "@/store/useStore";

interface InventoryItemCardProps {
  item: InventoryItem;
  onEdit?: () => void;
}

export function InventoryItemCard({ item }: InventoryItemCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [quantity, setQuantity] = useState(item.quantity.toString());
  const [threshold, setThreshold] = useState(item.threshold.toString());
  const [notes, setNotes] = useState(item.notes || "");

  const updateMutation = useUpdateInventoryItem();
  const deleteMutation = useDeleteInventoryItem();
  const currentUser = useStore((state) => state.currentUser);
  const isOwner = item.user_id === currentUser?.user_id;
  const isSharedFromOthers = item.shared && !isOwner;

  const isLowStock = item.quantity <= item.threshold;
  const isExpiringSoon =
    item.expiration_date &&
    new Date(item.expiration_date) <=
      new Date(Date.now() + 3 * 24 * 60 * 60 * 1000);

  const handleSave = async () => {
    try {
      if (!currentUser?.user_id) {
        toast.error("You must be logged in to update items");
        return;
      }

      await updateMutation.mutateAsync({
        userId: currentUser.user_id,
        itemId: item.item_id,
        updates: {
          quantity: parseFloat(quantity) || null,
          threshold: parseFloat(threshold) || null,
          notes: notes.trim() || null,
        },
      });
      setIsEditing(false);
      toast.success("Item updated successfully");
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to update item"
      );
    }
  };

  const handleDelete = async () => {
    if (
      !confirm(`Are you sure you want to delete "${item.name}"? This action cannot be undone.`)
    ) {
      return;
    }

    try {
      await deleteMutation.mutateAsync(item.item_id);
      toast.success("Item deleted successfully");
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to delete item"
      );
    }
  };

  const handleCancel = () => {
    setQuantity(item.quantity.toString());
    setThreshold(item.threshold.toString());
    setNotes(item.notes || "");
    setIsEditing(false);
  };

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return null;
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return null;
    }
  };

  return (
    <div
      className={cn(
        "rounded-lg border p-4 transition-colors",
        isLowStock
          ? "border-destructive/50 bg-destructive/5"
          : "border-border bg-card"
      )}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-sm text-foreground truncate">
              {item.name}
            </h3>
            {isLowStock && (
              <IconAlertTriangle className="size-4 text-destructive flex-shrink-0" />
            )}
          </div>

          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground mb-2">
            <span className="font-medium">{item.category}</span>
            {item.brand && <span>Brand: {item.brand}</span>}
            {item.price && <span>€{item.price.toFixed(2)}</span>}
            <Badge
              variant={item.shared ? (isOwner ? "default" : "secondary") : "outline"}
              className="text-xs"
            >
              {item.shared
                ? isOwner
                  ? "Shared"
                  : "Shared by flatmate"
                : "Personal"}
            </Badge>
          </div>

          {isEditing ? (
            <div className="space-y-3 mt-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label htmlFor={`qty-${item.item_id}`} className="text-xs">
                    Quantity
                  </Label>
                  <Input
                    id={`qty-${item.item_id}`}
                    type="number"
                    step="0.01"
                    min="0"
                    value={quantity}
                    onChange={(e) => setQuantity(e.target.value)}
                    className="h-8 text-xs"
                  />
                </div>
                <div>
                  <Label htmlFor={`thresh-${item.item_id}`} className="text-xs">
                    Threshold
                  </Label>
                  <Input
                    id={`thresh-${item.item_id}`}
                    type="number"
                    step="0.01"
                    min="0"
                    value={threshold}
                    onChange={(e) => setThreshold(e.target.value)}
                    className="h-8 text-xs"
                  />
                </div>
              </div>
              <div>
                <Label htmlFor={`notes-${item.item_id}`} className="text-xs">
                  Notes
                </Label>
                <Input
                  id={`notes-${item.item_id}`}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Optional notes..."
                  className="h-8 text-xs"
                />
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="default"
                  onClick={handleSave}
                  disabled={
                    updateMutation.isPending || deleteMutation.isPending
                  }
                  className="h-7 text-xs"
                >
                  <IconCheck className="size-3.5" />
                  Save
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={handleCancel}
                  disabled={
                    updateMutation.isPending || deleteMutation.isPending
                  }
                  className="h-7 text-xs"
                >
                  <IconX className="size-3.5" />
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-sm">
                <span className="text-foreground font-medium">
                  {item.quantity} {item.unit}
                </span>
                <span className="text-muted-foreground">/</span>
                <span className="text-muted-foreground text-xs">
                  Threshold: {item.threshold} {item.unit}
                </span>
              </div>
              {item.expiration_date && (
                <div
                  className={cn(
                    "text-xs",
                    isExpiringSoon ? "text-destructive" : "text-muted-foreground"
                  )}
                >
                  Expires: {formatDate(item.expiration_date)}
                </div>
              )}
              {item.notes && (
                <div className="text-xs text-muted-foreground mt-1">
                  {item.notes}
                </div>
              )}
            </div>
          )}
        </div>

        {!isEditing && (
          <div className="flex gap-1 flex-shrink-0">
            <Button
              size="icon"
              variant="ghost"
              className="h-8 w-8"
              onClick={() => setIsEditing(true)}
              title="Edit item"
            >
              <IconEdit className="size-4" />
            </Button>
            <Button
              size="icon"
              variant="ghost"
              className="h-8 w-8 text-destructive hover:text-destructive"
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
              title="Delete item"
            >
              <IconTrash className="size-4" />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}

