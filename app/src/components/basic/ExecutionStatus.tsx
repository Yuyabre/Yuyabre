import { motion } from "framer-motion";
import { IconLoader, IconCheck } from "@tabler/icons-react";
import { getFunctionDescription } from "@/lib/functionDescriptions";

interface ExecutionStatusProps {
  functionName: string;
  isDone?: boolean;
}

export function ExecutionStatus({
  functionName,
  isDone = false,
}: ExecutionStatusProps) {
  const description = getFunctionDescription(functionName, isDone);

  return (
    <motion.div
      className="flex items-center gap-2 px-3 py-2 bg-muted/50 rounded-md border border-border/50 mb-1"
      initial={{ opacity: 0, y: -5 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
    >
      {isDone ? (
        <IconCheck className="size-4 text-muted-foreground flex-shrink-0" />
      ) : (
        <IconLoader className="size-4 text-primary animate-spin flex-shrink-0" />
      )}
      <span className="text-sm text-muted-foreground font-medium">
        {description}
      </span>
    </motion.div>
  );
}
