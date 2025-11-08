import { Modal } from "../ui/Modal";

interface ExpensesModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ExpensesModal({ open, onOpenChange }: ExpensesModalProps) {
  return (
    <Modal open={open} onOpenChange={onOpenChange} title="Expenses">
      <div className="text-zinc-600 dark:text-zinc-400">
        Expenses view will be implemented here.
      </div>
    </Modal>
  );
}

