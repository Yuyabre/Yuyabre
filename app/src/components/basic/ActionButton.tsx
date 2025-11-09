import { motion } from "framer-motion";
import { Button } from "../ui/button";

interface ActionButtonProps {
  index: number;
  title: string;
  label: string;
  onClick: () => void;
}

export function ActionButton({
  index,
  title,
  label,
  onClick,
}: ActionButtonProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.01 * index }}
      className={index > 1 ? "hidden sm:block" : "block"}
    >
      <Button
        variant="outline"
        size="lg"
        onClick={onClick}
        className="w-full text-left flex flex-col items-start h-auto py-3"
      >
        <span className="font-medium">{title}</span>
        <span className="text-sm opacity-70">{label}</span>
      </Button>
    </motion.div>
  );
}
