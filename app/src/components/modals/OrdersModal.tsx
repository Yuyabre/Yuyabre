import { Modal } from "../ui/Modal";

interface OrdersModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function OrdersModal({ open, onOpenChange }: OrdersModalProps) {
  return (
    <Modal open={open} onOpenChange={onOpenChange} title="Orders">
      <div className="text-zinc-600 dark:text-zinc-400">
        Orders view will be implemented here.
      </div>
    </Modal>
  );
}

