import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
  type ReactElement,
} from "react";
import { flushSync } from "react-dom";
import { ChatMessages } from "./ChatMessages";
import { ChatInputForm } from "./ChatInputForm";
import { useActions } from "@/hooks/useActions";
import { useScrollToBottom } from "@/hooks/useScrollToBottom";
import { useWebSocket } from "@/providers/WebSocketProvider";
import { Message } from "@/components/basic/Message";
import { MessageRole, MessageType, type IMessage } from "@/types/chat";
import { websocketManager } from "@/lib/api/websocket";

const STREAM_CHUNK_DELAY = 30;

const generateId = (prefix: string) =>
  `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

const createUserMessage = (content: string): IMessage => ({
  id: generateId("user"),
  role: MessageRole.USER,
  type: MessageType.TEXT,
  content,
});

export function Chat() {
  const { sendMessage } = useActions();
  const { onMessage } = useWebSocket();

  const [input, setInput] = useState<string>("");
  const [staticMessages, setStaticMessages] = useState<IMessage[]>([]);
  const [streamingMessages, setStreamingMessages] = useState<
    Map<string, string>
  >(new Map());

  const cleanupFunctionsRef = useRef<Map<string, () => void>>(new Map());
  const streamQueuesRef = useRef<Map<string, Promise<void>>>(new Map());
  const inputRef = useRef<HTMLInputElement>(null);
  const [messagesContainerRef, messagesEndRef] =
    useScrollToBottom<HTMLDivElement>();

  const cancelExistingStreams = () => {
    if (cleanupFunctionsRef.current.size > 0) {
      console.log("Canceling existing streams", {
        activeStreams: cleanupFunctionsRef.current.size,
      });
      cleanupFunctionsRef.current.forEach((cleanup) => {
        try {
          cleanup();
        } catch (error) {
          console.warn("Error during stream cleanup", error);
        }
      });
      cleanupFunctionsRef.current.clear();
      streamQueuesRef.current.clear();
    }

    setStreamingMessages(new Map());
  };

  useEffect(() => {
    const cleanupAllConnections = () => {
      console.log("Cleaning up all WebSocket connections");
      cleanupFunctionsRef.current.forEach((cleanup) => cleanup());
      cleanupFunctionsRef.current.clear();
      websocketManager.close();
    };

    const handleBeforeUnload = () => {
      cleanupAllConnections();
    };

    const handleVisibilityChange = () => {
      if (document.hidden) {
        cleanupAllConnections();
      }
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      cleanupAllConnections();
      window.removeEventListener("beforeunload", handleBeforeUnload);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, []);

  useEffect(() => {
    const unsubscribe = onMessage((message) => {
      setStaticMessages((msgs) => [
        ...msgs,
        {
          id: message.id,
          role: message.role as MessageRole,
          type: message.type as MessageType,
          content: message.content,
          orderData: message.orderData,
        },
      ]);
    });

    return unsubscribe;
  }, [onMessage]);

  const messageNodes = useMemo(() => {
    const result: ReactElement[] = [];

    staticMessages.forEach((msg) => {
      if (!streamingMessages.has(msg.id)) {
        result.push(
          <Message
            key={msg.id}
            id={msg.id}
            role={msg.role}
            type={msg.type}
            content={msg.content}
            orderData={msg.orderData}
          />
        );
      }
    });

    streamingMessages.forEach((content, messageId) => {
      result.push(
        <Message
          key={messageId}
          id={messageId}
          role={MessageRole.ASSISTANT}
          type={MessageType.TEXT}
          content={content}
          {...({ isStreaming: true } as any)}
        />
      );
    });

    return result;
  }, [staticMessages, streamingMessages]);

  const isStreaming = streamingMessages.size > 0;

  const enqueueChunkUpdate = (messageId: string, updater: () => void): void => {
    const currentQueue =
      streamQueuesRef.current.get(messageId) ?? Promise.resolve();

    const nextQueue = currentQueue
      .catch(() => {
        // swallow previous errors to keep queue alive
      })
      .then(
        () =>
          new Promise<void>((resolve) => {
            setTimeout(() => {
              updater();
              resolve();
            }, STREAM_CHUNK_DELAY);
          })
      );

    streamQueuesRef.current.set(messageId, nextQueue);
  };

  const handleOrderApproved = (approvalMessage: string) => {
    setStaticMessages((msgs) => [
      ...msgs,
      {
        id: generateId("approval"),
        role: MessageRole.ASSISTANT,
        type: MessageType.TEXT,
        content: approvalMessage,
      },
    ]);
  };

  const handleStreamStart = (messageId: string, cleanup: () => void) => {
    console.log("Stream started for message:", messageId);
    setStreamingMessages((prev) => new Map(prev.set(messageId, "")));
    cleanupFunctionsRef.current.set(messageId, cleanup);
    streamQueuesRef.current.set(messageId, Promise.resolve());
  };

  const handleStreamChunk = (messageId: string, chunk: string) => {
    enqueueChunkUpdate(messageId, () => {
      setStreamingMessages((prev) => {
        const current = prev.get(messageId) || "";
        const updated = new Map(prev);
        updated.set(messageId, current + chunk);
        return updated;
      });
    });
  };

  const handleStreamComplete = (messageId: string, finalContent: string) => {
    console.log("Stream complete, final content:", finalContent);
    const cleanupFn = cleanupFunctionsRef.current.get(messageId);
    if (cleanupFn) {
      cleanupFn();
      cleanupFunctionsRef.current.delete(messageId);
    }

    const queue = streamQueuesRef.current.get(messageId) ?? Promise.resolve();
    queue
      .catch(() => {
        // ignore queue errors
      })
      .then(() => {
        streamQueuesRef.current.delete(messageId);
        flushSync(() => {
          setStreamingMessages((prev) => {
            const next = new Map(prev);
            next.delete(messageId);
            return next;
          });

          setStaticMessages((msgs) => {
            const exists = msgs.some((msg) => msg.id === messageId);
            if (exists) {
              console.warn("Message already exists, skipping:", messageId);
              return msgs;
            }

            return [
              ...msgs,
              {
                id: messageId,
                role: MessageRole.ASSISTANT,
                type: MessageType.TEXT,
                content: finalContent || "",
              },
            ];
          });
        });
      });
  };

  const handleStreamError = (messageId: string, error: Error) => {
    const cleanupFn = cleanupFunctionsRef.current.get(messageId);
    if (cleanupFn) {
      cleanupFn();
      cleanupFunctionsRef.current.delete(messageId);
    }

    const queue = streamQueuesRef.current.get(messageId) ?? Promise.resolve();
    queue
      .catch(() => {})
      .then(() => {
        streamQueuesRef.current.delete(messageId);
        setStreamingMessages((prev) => {
          const next = new Map(prev);
          next.delete(messageId);
          return next;
        });

        setStaticMessages((msgs) => [
          ...msgs,
          {
            id: generateId("error"),
            role: MessageRole.ASSISTANT,
            type: MessageType.TEXT,
            content: `Error: ${error.message}`,
          },
        ]);
      });
  };

  const handleSend = (content: string, userMessage?: IMessage) => {
    const text = content.trim();
    if (!text) {
      return;
    }

    cancelExistingStreams();

    if (userMessage) {
      flushSync(() => {
        setStaticMessages((messages) => [...messages, userMessage]);
      });
    }

    try {
      sendMessage(text, {
        onStreamStart: handleStreamStart,
        onChunk: handleStreamChunk,
        onComplete: handleStreamComplete,
        onError: handleStreamError,
      });
    } catch (error) {
      console.error("Error sending message:", error);
      const err =
        error instanceof Error ? error : new Error("Failed to send message");
      handleStreamError(generateId("send-error"), err);
    }
  };

  const handleSuggestedAction = (action: string) => {
    const userMessage = createUserMessage(action);
    handleSend(action, userMessage);
  };

  const handleFormSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (isStreaming) {
      return;
    }

    const trimmedInput = input.trim();
    if (!trimmedInput) {
      return;
    }

    setInput("");
    const userMessage = createUserMessage(trimmedInput);
    handleSend(trimmedInput, userMessage);
  };

  return (
    <div className="flex flex-row justify-center pb-20 h-full bg-background">
      <div className="flex flex-col justify-between gap-4">
        <ChatMessages
          messageNodes={messageNodes}
          messagesContainerRef={messagesContainerRef}
          messagesEndRef={messagesEndRef}
          onOrderApproved={handleOrderApproved}
          onSuggestedAction={handleSuggestedAction}
        />

        <ChatInputForm
          inputRef={inputRef as React.RefObject<HTMLInputElement>}
          inputValue={input}
          onInputChange={setInput}
          onSubmit={handleFormSubmit}
          isStreaming={isStreaming}
        />
      </div>
    </div>
  );
}
