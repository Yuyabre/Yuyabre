import { Modal } from "../basic/Modal";

interface OrdersModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function OrdersModal({ open, onOpenChange }: OrdersModalProps) {
  return (
    <Modal open={open} onOpenChange={onOpenChange} title="Orders">
      <div className="text-muted-foreground">
        Orders view will be implemented here.
      </div>
    </Modal>
  );
}
