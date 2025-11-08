import { Modal } from "../ui/Modal";

interface ExpensesModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ExpensesModal({ open, onOpenChange }: ExpensesModalProps) {
  return (
    <Modal open={open} onOpenChange={onOpenChange} title="Expenses">
      <div className="text-theme-tertiary">
        Expenses view will be implemented here.
      </div>
    </Modal>
  );
}

