"use client";

import { motion } from "framer-motion";
import { IconRobotFace, IconUser } from "@tabler/icons-react";
import { Markdown } from "./Markdown";
import { IMessage } from "@/types/chat";

export const TextStreamMessage = ({ content }: { content: string }) => {
  return (
    <motion.div
      className={`flex flex-row gap-4 px-4 w-full md:w-[500px] md:px-0 first-of-type:pt-20`}
      initial={{ y: 5, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
    >
      <div className="size-[24px] flex flex-col justify-center items-center flex-shrink-0 text-zinc-400">
        <IconRobotFace />
      </div>

      <div className="flex flex-col gap-1 w-full">
        <div className="text-zinc-800 dark:text-zinc-300 flex flex-col gap-4">
          <Markdown>{content}</Markdown>
        </div>
      </div>
    </motion.div>
  );
};

export const Message = ({ id, role, content, timestamp }: IMessage) => {
  return (
    <motion.div
      className={`flex flex-row gap-4 px-4 w-full md:w-[500px] md:px-0 first-of-type:pt-20`}
      initial={{ y: 5, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      key={id}
    >
      <div className="size-[24px] flex flex-col justify-center items-center flex-shrink-0 text-zinc-400">
        {role === "assistant" ? <IconRobotFace /> : <IconUser />}
      </div>

      <div className="flex flex-col gap-1 w-full">
        <div className="text-zinc-800 dark:text-zinc-300 flex flex-col gap-4">
          <Markdown>{content}</Markdown>
        </div>
      </div>
    </motion.div>
  );
};
