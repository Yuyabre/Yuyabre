import { Modal } from "../ui/Modal";

interface OrdersModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function OrdersModal({ open, onOpenChange }: OrdersModalProps) {
  return (
    <Modal open={open} onOpenChange={onOpenChange} title="Orders">
      <div className="text-theme-tertiary">
        Orders view will be implemented here.
      </div>
    </Modal>
  );
}

