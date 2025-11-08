import { Modal } from "../ui/Modal";

interface InventoryModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function InventoryModal({ open, onOpenChange }: InventoryModalProps) {
  return (
    <Modal open={open} onOpenChange={onOpenChange} title="Inventory">
      <div className="text-theme-tertiary">
        Inventory view will be implemented here.
      </div>
    </Modal>
  );
}

