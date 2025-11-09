import { useState, type FormEvent } from "react";
import { toast } from "sonner";
import type { InventoryItemCreate } from "@/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { IconPlus, IconX } from "@tabler/icons-react";
import { useCreateInventoryItem } from "@/lib/queries";
import { useStore } from "@/store/useStore";

interface InventoryItemFormProps {
  onSuccess?: () => void;
  onCancel?: () => void;
}

const COMMON_CATEGORIES = [
  "Dairy",
  "Vegetables",
  "Fruits",
  "Meat",
  "Bakery",
  "Beverages",
  "Snacks",
  "Frozen",
  "Pantry",
  "Other",
];

const COMMON_UNITS = [
  "pieces",
  "kg",
  "g",
  "liters",
  "ml",
  "packages",
  "boxes",
  "bottles",
];

export function InventoryItemForm({
  onSuccess,
  onCancel,
}: InventoryItemFormProps) {
  const { currentUser } = useStore();
  const [name, setName] = useState("");
  const [category, setCategory] = useState("");
  const [customCategory, setCustomCategory] = useState("");
  const [quantity, setQuantity] = useState("");
  const [unit, setUnit] = useState("");
  const [customUnit, setCustomUnit] = useState("");
  const [threshold, setThreshold] = useState("1");
  const [shared, setShared] = useState(true);
  const [brand, setBrand] = useState("");
  const [price, setPrice] = useState("");

  const createMutation = useCreateInventoryItem();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!name.trim()) {
      toast.error("Name is required");
      return;
    }

    if (!category && !customCategory.trim()) {
      toast.error("Category is required");
      return;
    }

    if (!quantity || parseFloat(quantity) < 0) {
      toast.error("Valid quantity is required");
      return;
    }

    if (!unit && !customUnit.trim()) {
      toast.error("Unit is required");
      return;
    }

    if (!currentUser?.user_id) {
      toast.error("You must be logged in to create inventory items");
      return;
    }

    try {
      const itemData: InventoryItemCreate = {
        name: name.trim(),
        category: customCategory.trim() || category,
        quantity: parseFloat(quantity),
        unit: customUnit.trim() || unit,
        threshold: parseFloat(threshold) || 1,
        shared,
        brand: brand.trim() || null,
        price: price ? parseFloat(price) : null,
      };

      await createMutation.mutateAsync({
        userId: currentUser.user_id,
        item: itemData,
      });
      toast.success("Item added successfully");

      // Reset form
      setName("");
      setCategory("");
      setCustomCategory("");
      setQuantity("");
      setUnit("");
      setCustomUnit("");
      setThreshold("1");
      setShared(true);
      setBrand("");
      setPrice("");

      onSuccess?.();
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to create item"
      );
    }
  };

  const useCustomCategory = category === "__custom__";
  const useCustomUnit = unit === "__custom__";

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="col-span-2">
          <Label htmlFor="name">Name *</Label>
          <Input
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., Milk, Bread, Eggs"
            required
          />
        </div>

        <div>
          <Label htmlFor="category">Category *</Label>
          <select
            id="category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-xs transition-colors focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] outline-none"
            required
          >
            <option value="">Select category</option>
            {COMMON_CATEGORIES.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
            <option value="__custom__">Custom...</option>
          </select>
        </div>

        {useCustomCategory && (
          <div>
            <Label htmlFor="customCategory">Custom Category *</Label>
            <Input
              id="customCategory"
              value={customCategory}
              onChange={(e) => setCustomCategory(e.target.value)}
              placeholder="Enter category"
              required
            />
          </div>
        )}

        <div>
          <Label htmlFor="quantity">Quantity *</Label>
          <Input
            id="quantity"
            type="number"
            step="0.01"
            min="0"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            placeholder="0"
            required
          />
        </div>

        <div>
          <Label htmlFor="unit">Unit *</Label>
          <select
            id="unit"
            value={unit}
            onChange={(e) => setUnit(e.target.value)}
            className="h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-xs transition-colors focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] outline-none"
            required
          >
            <option value="">Select unit</option>
            {COMMON_UNITS.map((u) => (
              <option key={u} value={u}>
                {u}
              </option>
            ))}
            <option value="__custom__">Custom...</option>
          </select>
        </div>

        {useCustomUnit && (
          <div>
            <Label htmlFor="customUnit">Custom Unit *</Label>
            <Input
              id="customUnit"
              value={customUnit}
              onChange={(e) => setCustomUnit(e.target.value)}
              placeholder="Enter unit"
              required
            />
          </div>
        )}

        <div>
          <Label htmlFor="threshold">Low Stock Threshold</Label>
          <Input
            id="threshold"
            type="number"
            step="0.01"
            min="0"
            value={threshold}
            onChange={(e) => setThreshold(e.target.value)}
            placeholder="1"
          />
        </div>

        <div>
          <Label htmlFor="brand">Brand (optional)</Label>
          <Input
            id="brand"
            value={brand}
            onChange={(e) => setBrand(e.target.value)}
            placeholder="e.g., Melkunie"
          />
        </div>

        <div>
          <Label htmlFor="price">Price (optional)</Label>
          <Input
            id="price"
            type="number"
            step="0.01"
            min="0"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            placeholder="0.00"
          />
        </div>

        <div className="col-span-2 flex items-center gap-2">
          <input
            type="checkbox"
            id="shared"
            checked={shared}
            onChange={(e) => setShared(e.target.checked)}
            className="h-4 w-4 rounded border-input"
          />
          <Label htmlFor="shared" className="font-normal cursor-pointer">
            Shared with household
          </Label>
        </div>
      </div>

      <div className="flex gap-2 justify-end">
        {onCancel && (
          <Button
            type="button"
            variant="ghost"
            onClick={onCancel}
            disabled={createMutation.isPending}
          >
            <IconX className="size-4" />
            Cancel
          </Button>
        )}
        <Button type="submit" disabled={createMutation.isPending}>
          <IconPlus className="size-4" />
          Add Item
        </Button>
      </div>
    </form>
  );
}

