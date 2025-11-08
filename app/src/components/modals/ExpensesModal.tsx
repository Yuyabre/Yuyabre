import { Modal } from "../basic/Modal";

interface ExpensesModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ExpensesModal({ open, onOpenChange }: ExpensesModalProps) {
  return (
    <Modal open={open} onOpenChange={onOpenChange} title="Expenses">
      <div className="text-muted-foreground">
        Expenses view will be implemented here.
      </div>
    </Modal>
  );
}
