import { motion } from "framer-motion";
import { ReactNode } from "react";

interface ActionButtonProps {
  index: number;
  title: string;
  label: string;
  onClick: () => void;
  children?: ReactNode;
}

export function ActionButton({
  index,
  title,
  label,
  onClick,
  children,
}: ActionButtonProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.01 * index }}
      className={index > 1 ? "hidden sm:block" : "block"}
    >
      <button
        onClick={onClick}
        className="w-full text-left border border-zinc-200 dark:border-zinc-800 text-zinc-800 dark:text-zinc-300 rounded-lg p-2 text-sm hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors flex flex-col"
      >
        <span className="font-medium">{title}</span>
        <span className="text-zinc-500 dark:text-zinc-400">{label}</span>
      </button>
    </motion.div>
  );
}
