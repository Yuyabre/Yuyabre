import { motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import { LogoIcon } from "@/components/icons/Logo";
import {
  IconSparkles,
  IconShoppingCart,
  IconClipboardHeart,
  IconDeviceAnalytics,
} from "@tabler/icons-react";

const highlights = [
  {
    icon: IconSparkles,
    title: "What's in the inventory?",
    subtitle: "See all groceries at home",
    prompt: "What's in the inventory?",
  },
  {
    icon: IconShoppingCart,
    title: "Order groceries",
    subtitle: "Plan the next delivery",
    prompt: "Order 2 liters of milk",
  },
  {
    icon: IconClipboardHeart,
    title: "Track expenses",
    subtitle: "Review Splitwise activity",
    prompt: "Show me pending expenses",
  },
  {
    icon: IconDeviceAnalytics,
    title: "Catch low stock",
    subtitle: "Find items running low",
    prompt: "Check low stock items",
  },
];

const promptMessages = [
  "What groceries are running low?",
  "Which orders are pending delivery?",
  "Do we owe anything on Splitwise?",
  "Suggest a dinner plan for tonight.",
];

interface ChatEmptyStateProps {
  onSuggestedAction?: (prompt: string) => void;
}

export function ChatEmptyState({ onSuggestedAction }: ChatEmptyStateProps) {
  const [promptIndex, setPromptIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setPromptIndex((prev) => (prev + 1) % promptMessages.length);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const promptMessage = useMemo(
    () => promptMessages[promptIndex],
    [promptIndex]
  );

  return (
    <div className="flex flex-col items-center gap-6 px-6 py-12 text-center">
      <motion.div
        initial={{ scale: 0.85, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: "spring", stiffness: 120, damping: 12 }}
        className="relative"
      >
        <motion.div
          animate={{
            boxShadow: [
              "0 0 0 0 rgba(37, 99, 235, 0.25)",
              "0 0 0 14px rgba(37, 99, 235, 0)",
            ],
          }}
          transition={{ repeat: Infinity, duration: 2.8, ease: "easeInOut" }}
          className="absolute inset-0 rounded-3xl"
        />
        <div className="flex h-20 w-20 items-center justify-center rounded-3xl bg-gradient-to-br from-primary/15 via-sky-500/20 to-primary/5 text-primary shadow-[0_10px_45px_-20px_rgba(37,99,235,0.65)]">
          <LogoIcon className="h-12 w-12" />
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15, duration: 0.4 }}
        className="space-y-2"
      >
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">
          Welcome to Yuyabre
        </h2>
        <p className="text-sm text-muted-foreground">
          Your shared flat concierge for groceries, expenses, and everything in
          between.
        </p>
      </motion.div>

      <div className="grid w-full max-w-2xl gap-3 rounded-3xl border border-primary/20 bg-gradient-to-b from-background/70 via-sky-500/[0.04] to-background/90 p-4 shadow-[0_18px_40px_-25px_rgba(37,99,235,0.65)] sm:grid-cols-2">
        {highlights.map((highlight, index) => {
          const Icon = highlight.icon;
          const handleClick = () => {
            onSuggestedAction?.(highlight.prompt);
          };

          return (
            <motion.button
              key={highlight.title}
              type="button"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.25 + index * 0.1, duration: 0.35 }}
              className="group relative flex w-full items-center gap-3 overflow-hidden rounded-2xl border border-primary/15 bg-gradient-to-br from-background/95 via-sky-500/[0.04] to-background/90 px-4 py-3 text-left transition hover:border-primary/40 hover:bg-gradient-to-br hover:from-primary/10 hover:via-sky-500/10 hover:to-primary/5"
              onClick={handleClick}
            >
              <span className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl border border-primary/30 bg-gradient-to-br from-primary/25 via-sky-500/25 to-primary/10 text-primary shadow-[0_12px_30px_-20px_rgba(37,99,235,0.75)] group-hover:shadow-[0_12px_35px_-18px_rgba(37,99,235,0.95)]">
                <Icon className="size-4" />
              </span>
              <span className="flex flex-col gap-1">
                <span className="text-sm font-medium text-foreground">
                  {highlight.title}
                </span>
                <span className="text-xs text-muted-foreground">
                  {highlight.subtitle}
                </span>
              </span>
            </motion.button>
          );
        })}
      </div>

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5, duration: 0.35 }}
        className="relative w-full max-w-xl"
      >
        <motion.button
          type="button"
          onClick={() => onSuggestedAction?.(promptMessage)}
          animate={{ opacity: [0.65, 1, 0.65], y: [0, -3, 0] }}
          transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
          className="w-full rounded-2xl border border-primary/20 bg-gradient-to-r from-primary/5 via-sky-500/10 to-primary/5 p-4 text-left shadow-[0_15px_35px_-25px_rgba(37,99,235,0.85)] backdrop-blur transition hover:border-primary/40"
        >
          <p className="text-sm text-muted-foreground">
            Try asking <span className="text-foreground">“{promptMessage}”</span>
          </p>
        </motion.button>
      </motion.div>
    </div>
  );
}
