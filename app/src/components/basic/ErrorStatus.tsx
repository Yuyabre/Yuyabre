import { motion } from "framer-motion";
import { IconAlertCircle } from "@tabler/icons-react";

interface ErrorStatusProps {
  message: string;
}

export function ErrorStatus({ message }: ErrorStatusProps) {
  return (
    <motion.div
      className="flex items-center gap-2 px-3 py-2 bg-destructive/10 rounded-md border border-destructive/20 mb-1"
      initial={{ opacity: 0, y: -5 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
    >
      <IconAlertCircle className="size-4 text-destructive flex-shrink-0" />
      <span className="text-sm text-destructive font-medium">
        {message}
      </span>
    </motion.div>
  );
}

