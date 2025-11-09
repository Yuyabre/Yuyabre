import { useState, useMemo } from "react";
import { Modal } from "@/components/basic/Modal";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import {
  IconPlus,
  IconSearch,
  IconFilter,
  IconX,
} from "@tabler/icons-react";
import { useInventory } from "@/lib/queries";
import { InventoryItemList } from "./InventoryItemList";
import { InventoryItemForm } from "./InventoryItemForm";

interface InventoryModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

type StockFilter = "all" | "low" | "normal";

export function InventoryModal({ open, onOpenChange }: InventoryModalProps) {
  const [showForm, setShowForm] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterCategory, setFilterCategory] = useState<string>("");
  const [stockFilter, setStockFilter] = useState<StockFilter>("all");

  const { data: items = [], isLoading } = useInventory();

  const categories = useMemo(() => {
    const cats = new Set(items.map((item) => item.category));
    return Array.from(cats).sort();
  }, [items]);

  const filteredItems = useMemo(() => {
    let filtered = [...items];

    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (item) =>
          item.name.toLowerCase().includes(query) ||
          item.category.toLowerCase().includes(query) ||
          item.brand?.toLowerCase().includes(query) ||
          item.notes?.toLowerCase().includes(query)
      );
    }

    if (stockFilter === "low") {
      filtered = filtered.filter((item) => item.quantity <= item.threshold);
    } else if (stockFilter === "normal") {
      filtered = filtered.filter((item) => item.quantity > item.threshold);
    }

    if (filterCategory) {
      filtered = filtered.filter(
        (item) => item.category.toLowerCase() === filterCategory.toLowerCase()
      );
    }

    // Sort by low stock first, then by name
    return filtered.sort((a, b) => {
      const aLowStock = a.quantity <= a.threshold;
      const bLowStock = b.quantity <= b.threshold;
      if (aLowStock !== bLowStock) {
        return aLowStock ? -1 : 1;
      }
      return a.name.localeCompare(b.name);
    });
  }, [items, searchQuery, filterCategory, stockFilter]);

  const lowStockCount = useMemo(
    () => items.filter((item) => item.quantity <= item.threshold).length,
    [items]
  );

  const normalStockCount = useMemo(
    () => items.filter((item) => item.quantity > item.threshold).length,
    [items]
  );

  const handleFormSuccess = () => {
    setShowForm(false);
  };

  const handleClose = () => {
    setShowForm(false);
    setSearchQuery("");
    setFilterCategory("");
    setStockFilter("all");
    onOpenChange(false);
  };

  return (
    <Modal
      open={open}
      onOpenChange={handleClose}
      title="Inventory"
      description="Manage your household inventory items"
    >
      <div className="space-y-4">
        {/* Header Actions */}
        <div className="flex items-center justify-between gap-2">
          <div className="flex-1 relative">
            <IconSearch className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search items..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
          <Button
            variant="default"
            onClick={() => setShowForm(!showForm)}
            className="shrink-0"
          >
            {showForm ? (
              <>
                <IconX className="size-4" />
                Cancel
              </>
            ) : (
              <>
                <IconPlus className="size-4" />
                Add Item
              </>
            )}
          </Button>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-2">
            <IconFilter className="size-4 text-muted-foreground" />
            <span className="text-xs text-muted-foreground">Filters:</span>
          </div>

          <Button
            variant={stockFilter === "low" ? "default" : "outline"}
            size="sm"
            onClick={() =>
              setStockFilter(stockFilter === "low" ? "all" : "low")
            }
            className="text-xs"
          >
            Low Stock {lowStockCount > 0 && `(${lowStockCount})`}
          </Button>

          <Button
            variant={stockFilter === "normal" ? "default" : "outline"}
            size="sm"
            onClick={() =>
              setStockFilter(stockFilter === "normal" ? "all" : "normal")
            }
            className="text-xs"
          >
            Normal Stock {normalStockCount > 0 && `(${normalStockCount})`}
          </Button>

          {categories.length > 0 && (
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="h-8 rounded-md border border-input bg-transparent px-2 py-1 text-xs shadow-xs transition-colors focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] outline-none"
            >
              <option value="">All Categories</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          )}

          {(filterCategory || stockFilter !== "all") && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setFilterCategory("");
                setStockFilter("all");
              }}
              className="text-xs h-8"
            >
              Clear filters
            </Button>
          )}
        </div>

        <Separator />

        {/* Add Item Form */}
        {showForm && (
          <div className="rounded-lg border border-border bg-muted/40 p-4">
            <h3 className="text-sm font-semibold mb-3">Add New Item</h3>
            <InventoryItemForm
              onSuccess={handleFormSuccess}
              onCancel={() => setShowForm(false)}
            />
          </div>
        )}

        {/* Items List */}
        {!showForm && (
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold">
                Items ({filteredItems.length})
              </h3>
            </div>
            <InventoryItemList items={filteredItems} isLoading={isLoading} />
          </div>
        )}
      </div>
    </Modal>
  );
}

