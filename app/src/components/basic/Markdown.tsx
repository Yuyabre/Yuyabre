import React, { useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ExecutionStatus } from "./ExecutionStatus";
import { ErrorStatus } from "./ErrorStatus";

export const NonMemoizedMarkdown = ({ children }: { children: string }) => {
  // Parse execution messages, error messages, and split content
  const parsedContent = useMemo(() => {
    const parts: Array<{ 
      type: "execution" | "error" | "text"; 
      content: string; 
      functionName?: string;
      errorMessage?: string;
      isDone?: boolean;
    }> = [];
    let lastIndex = 0;

    // Find all execution messages
    const executionRegex = /\[Executing\s+(\w+)\s*\.\.\.\]/g;
    let match;
    const executionMatches: Array<{ index: number; length: number; functionName: string }> = [];

    // Collect all execution matches first
    while ((match = executionRegex.exec(children)) !== null) {
      executionMatches.push({
        index: match.index,
        length: match[0].length,
        functionName: match[1],
      });
    }

    // Find all error messages (Error: message)
    const errorRegex = /Error:\s*([^\n]+)/g;
    const errorMatches: Array<{ index: number; length: number; message: string }> = [];
    while ((match = errorRegex.exec(children)) !== null) {
      errorMatches.push({
        index: match.index,
        length: match[0].length,
        message: match[1].trim(),
      });
    }

    // Combine all matches and sort by index
    const allMatches: Array<{
      index: number;
      length: number;
      type: "execution" | "error";
      functionName?: string;
      errorMessage?: string;
    }> = [
      ...executionMatches.map((m) => ({
        ...m,
        type: "execution" as const,
        functionName: m.functionName,
      })),
      ...errorMatches.map((m) => ({
        ...m,
        type: "error" as const,
        errorMessage: m.message,
      })),
    ].sort((a, b) => a.index - b.index);

    // Process each match
    allMatches.forEach((currentMatch, matchIndex) => {
      // Add text before current match
      if (currentMatch.index > lastIndex) {
        const textBefore = children.slice(lastIndex, currentMatch.index);
        if (textBefore.trim()) {
          parts.push({ type: "text", content: textBefore });
        }
      }

      if (currentMatch.type === "execution") {
        // Check if this execution is done
        // It's done if there's content after it, or if there's another match after it
        const executionEnd = currentMatch.index + currentMatch.length;
        const nextMatchIndex = matchIndex < allMatches.length - 1 
          ? allMatches[matchIndex + 1].index 
          : children.length;
        
        const contentAfter = children.slice(executionEnd, nextMatchIndex).trim();
        const isDone = contentAfter.length > 0 || matchIndex < allMatches.length - 1;

        // Add execution message
        parts.push({
          type: "execution",
          content: children.slice(currentMatch.index, executionEnd),
          functionName: currentMatch.functionName,
          isDone,
        });
      } else if (currentMatch.type === "error") {
        // Add error message
        parts.push({
          type: "error",
          content: children.slice(currentMatch.index, currentMatch.index + currentMatch.length),
          errorMessage: currentMatch.errorMessage,
        });
      }

      lastIndex = currentMatch.index + currentMatch.length;
    });

    // Add remaining text
    if (lastIndex < children.length) {
      const textAfter = children.slice(lastIndex);
      if (textAfter.trim()) {
        parts.push({ type: "text", content: textAfter });
      }
    }

    // If no special messages found, return original content as text
    if (parts.length === 0) {
      return [{ type: "text" as const, content: children }];
    }

    return parts;
  }, [children]);

  const components = {
    code: ({ node, inline, className, children, ...props }: any) => {
      const match = /language-(\w+)/.exec(className || "");
      return !inline && match ? (
        <pre
          {...props}
          className={`${className} text-sm w-[80dvw] md:max-w-[500px] overflow-x-scroll bg-muted p-2 rounded mt-2`}
        >
          <code className={match[1]}>{children}</code>
        </pre>
      ) : (
        <code
          className={`${className} text-sm bg-muted py-0.5 px-1 rounded`}
          {...props}
        >
          {children}
        </code>
      );
    },
    ol: ({ node, children, ...props }: any) => {
      return (
        <ol className="list-decimal list-inside ml-4" {...props}>
          {children}
        </ol>
      );
    },
    li: ({ node, children, ...props }: any) => {
      return (
        <li className="py-1" {...props}>
          {children}
        </li>
      );
    },
    ul: ({ node, children, ...props }: any) => {
      return (
        <ul className="list-decimal list-inside ml-4" {...props}>
          {children}
        </ul>
      );
    },
    strong: ({ node, children, ...props }: any) => {
      return (
        <span className="font-semibold" {...props}>
          {children}
        </span>
      );
    },
  };

  return (
    <div className="flex flex-col gap-2">
      {parsedContent.map((part, index) => {
        if (part.type === "execution" && part.functionName) {
          return (
            <ExecutionStatus 
              key={`exec-${index}`} 
              functionName={part.functionName}
              isDone={part.isDone}
            />
          );
        }
        if (part.type === "error" && part.errorMessage) {
          return (
            <ErrorStatus 
              key={`error-${index}`} 
              message={part.errorMessage}
            />
          );
        }
        return (
          <ReactMarkdown
            key={`text-${index}`}
            remarkPlugins={[remarkGfm]}
            components={components}
          >
            {part.content}
          </ReactMarkdown>
        );
      })}
    </div>
  );
};

export const Markdown = React.memo(
  NonMemoizedMarkdown,
  (prevProps, nextProps) => prevProps.children === nextProps.children
);
