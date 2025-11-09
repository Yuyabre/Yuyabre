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
import { useUserInventory } from "@/lib/queries";
import { useStore } from "@/store/useStore";
import { InventoryItemList } from "./InventoryItemList";
import { InventoryItemForm } from "./InventoryItemForm";

interface InventoryModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  // userId and userName are kept for backward compatibility but not used
  // We only manage the current user's inventory
  userId?: string | null;
  userName?: string | null;
}

type StockFilter = "all" | "low" | "normal";

export function InventoryModal({ open, onOpenChange, userId, userName }: InventoryModalProps) {
  const { currentUser } = useStore();
  const [showForm, setShowForm] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterCategory, setFilterCategory] = useState<string>("");
  const [stockFilter, setStockFilter] = useState<StockFilter>("all");

  // Always use current user's ID - we only manage our own inventory
  const { data: items = [], isLoading } = useUserInventory(currentUser?.user_id ?? null);

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

  const modalTitle = "Inventory";
  const modalDescription = "Manage your inventory items";

  return (
    <Modal
      open={open}
      onOpenChange={handleClose}
      title={modalTitle}
      description={modalDescription}
    >
      <div className="space-y-4">
        <div className="rounded-2xl border border-primary/15 bg-gradient-to-br from-primary/5 via-sky-500/5 to-background p-4 shadow-[0_18px_40px_-28px_rgba(37,99,235,0.55)]">
          {/* Header Actions */}
          <div className="flex items-center justify-between gap-2">
            <div className="relative flex-1">
              <IconSearch className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-primary" />
              <Input
                type="text"
                placeholder="Search items..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 border-primary/30 focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/30"
              />
            </div>
            {currentUser && (
              <Button
                variant="default"
                onClick={() => setShowForm(!showForm)}
                className="shrink-0 rounded-xl border border-primary/30 bg-primary/90 shadow-[0_12px_30px_-18px_rgba(37,99,235,0.85)] hover:bg-primary/80"
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
            )}
          </div>

          {/* Filters */}
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-2 rounded-xl border border-primary/20 bg-primary/5 px-3 py-1">
              <IconFilter className="size-4 text-primary" />
              <span className="text-xs font-medium text-primary">Filters</span>
            </div>

            <Button
              variant={stockFilter === "low" ? "default" : "outline"}
              size="sm"
              onClick={() =>
                setStockFilter(stockFilter === "low" ? "all" : "low")
              }
              className="rounded-lg border border-primary/20 text-xs shadow-sm hover:border-primary/40"
            >
              Low Stock {lowStockCount > 0 && `(${lowStockCount})`}
            </Button>

            <Button
              variant={stockFilter === "normal" ? "default" : "outline"}
              size="sm"
              onClick={() =>
                setStockFilter(stockFilter === "normal" ? "all" : "normal")
              }
              className="rounded-lg border border-primary/20 text-xs shadow-sm hover:border-primary/40"
            >
              Normal Stock {normalStockCount > 0 && `(${normalStockCount})`}
            </Button>

            {categories.length > 0 && (
              <select
                value={filterCategory}
                onChange={(e) => setFilterCategory(e.target.value)}
                className="h-8 rounded-lg border border-primary/25 bg-background px-2 py-1 text-xs shadow-sm transition focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/40"
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
                className="h-8 rounded-lg text-xs text-primary hover:bg-primary/10"
              >
                Clear filters
              </Button>
            )}
          </div>
        </div>

        <Separator className="border-primary/15" />

        {/* Add Item Form */}
        {currentUser && showForm && (
          <div className="rounded-2xl border border-primary/15 bg-gradient-to-br from-primary/5 via-sky-500/5 to-background p-4 shadow-sm">
            <h3 className="mb-3 text-sm font-semibold text-foreground">Add New Item</h3>
            <InventoryItemForm
              onSuccess={handleFormSuccess}
              onCancel={() => setShowForm(false)}
            />
          </div>
        )}

        {/* Items List */}
        {!showForm && (
          <div className="rounded-2xl border border-primary/10 bg-gradient-to-br from-background via-sky-500/5 to-background/95 p-4 shadow-[0_12px_35px_-30px_rgba(37,99,235,0.6)]">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-foreground">
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

