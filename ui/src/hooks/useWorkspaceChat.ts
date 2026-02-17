/**
 * Hook for managing workspace chat WebSocket connection.
 *
 * Forked from useAssistantChat with workspace-specific differences:
 * - WebSocket URL targets /api/workspace/ws (no project name)
 * - Tracks token usage (totalTokens, contextWindow) from server messages
 * - start() accepts optional workingDirectory parameter
 * - Expanded tool call descriptions for Write, Edit, and Bash tools
 * - No structured question/answer flow (no MCP ask_user tool)
 */

import { useState, useCallback, useRef, useEffect } from "react";
import type { ChatMessage, WorkspaceChatServerMessage, PendingInjection } from "../lib/types";

type ConnectionStatus = "disconnected" | "connecting" | "connected" | "error";

interface UseWorkspaceChatOptions {
  onError?: (error: string) => void;
}

interface UseWorkspaceChatReturn {
  messages: ChatMessage[];
  isLoading: boolean;
  connectionStatus: ConnectionStatus;
  conversationId: number | null;
  totalTokens: number;
  contextWindow: number;
  contextBudget: {
    messageTokens: number;
    summaryTokens: number;
    messageCount: number;
  };
  pendingInjection: PendingInjection | null;
  setPendingInjection: (injection: PendingInjection | null) => void;
  start: (conversationId?: number | null, workingDirectory?: string, initialMessage?: string) => void;
  sendMessage: (content: string) => void;
  disconnect: () => void;
  clearMessages: () => void;
}

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}

/**
 * Hook for managing a workspace chat session over WebSocket.
 *
 * Handles connection lifecycle, message streaming, tool call descriptions,
 * token usage tracking, and automatic reconnection with exponential backoff.
 */
export function useWorkspaceChat({
  onError,
}: UseWorkspaceChatOptions = {}): UseWorkspaceChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] =
    useState<ConnectionStatus>("disconnected");
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [totalTokens, setTotalTokens] = useState(0);
  const [contextWindow, setContextWindow] = useState(1_000_000);
  const [contextBudget, setContextBudget] = useState<{
    messageTokens: number;
    summaryTokens: number;
    messageCount: number;
  }>({
    messageTokens: 0,
    summaryTokens: 0,
    messageCount: 0,
  });
  const [pendingInjection, setPendingInjection] = useState<PendingInjection | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const currentAssistantMessageRef = useRef<string | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 3;
  const pingIntervalRef = useRef<number | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const checkAndSendTimeoutRef = useRef<number | null>(null);
  const pendingFirstMessageRef = useRef<string | null>(null);

  // Clean up all timers and the WebSocket on unmount
  useEffect(() => {
    return () => {
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (checkAndSendTimeoutRef.current) {
        clearTimeout(checkAndSendTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
      currentAssistantMessageRef.current = null;
    };
  }, []);

  const connect = useCallback(() => {
    // Prevent multiple connection attempts
    if (
      wsRef.current?.readyState === WebSocket.OPEN ||
      wsRef.current?.readyState === WebSocket.CONNECTING
    ) {
      return;
    }

    setConnectionStatus("connecting");

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/api/workspace/ws`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnectionStatus("connected");
      reconnectAttempts.current = 0;

      // Start ping interval to keep the connection alive
      pingIntervalRef.current = window.setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "ping" }));
        }
      }, 30000);
    };

    ws.onclose = () => {
      setConnectionStatus("disconnected");
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = null;
      }

      // Attempt reconnection with exponential backoff if not intentionally closed
      if (reconnectAttempts.current < maxReconnectAttempts) {
        reconnectAttempts.current++;
        const delay = Math.min(
          1000 * Math.pow(2, reconnectAttempts.current),
          10000,
        );
        reconnectTimeoutRef.current = window.setTimeout(connect, delay);
      }
    };

    ws.onerror = () => {
      setConnectionStatus("error");
      onError?.("WebSocket connection error");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WorkspaceChatServerMessage;
        if (import.meta.env.DEV) {
          console.debug('[useWorkspaceChat] Received WebSocket message:', data.type, data);
        }

        switch (data.type) {
          case "text": {
            // Append text to current assistant message or create a new one
            setMessages((prev) => {
              const lastMessage = prev[prev.length - 1];
              if (
                lastMessage?.role === "assistant" &&
                lastMessage.isStreaming
              ) {
                return [
                  ...prev.slice(0, -1),
                  {
                    ...lastMessage,
                    content: lastMessage.content + data.content,
                  },
                ];
              } else {
                currentAssistantMessageRef.current = generateId();
                return [
                  ...prev,
                  {
                    id: currentAssistantMessageRef.current,
                    role: "assistant",
                    content: data.content,
                    timestamp: new Date(),
                    isStreaming: true,
                  },
                ];
              }
            });
            break;
          }

          case "tool_call": {
            const toolDescription = describeToolCall(data.tool, data.input);

            setMessages((prev) => [
              ...prev,
              {
                id: generateId(),
                role: "system",
                content: toolDescription,
                timestamp: new Date(),
              },
            ]);
            break;
          }

          case "token_usage": {
            const tokenData = data as { total_tokens: number; context_window: number };
            setTotalTokens(tokenData.total_tokens);
            setContextWindow(tokenData.context_window);
            setContextBudget(prev => ({
              ...prev,
              messageTokens: tokenData.total_tokens,
            }));
            break;
          }

          case "token_update": {
            const updateData = data as { token_count: number; message_count: number };
            setContextBudget(prev => ({
              ...prev,
              messageTokens: updateData.token_count ?? prev.messageTokens,
              messageCount: updateData.message_count ?? prev.messageCount,
            }));
            break;
          }

          case "conversation_created": {
            setConversationId(data.conversation_id);
            break;
          }

          case "response_done": {
            // If there's a queued first message (from start-with-message),
            // send it now that the session is ready instead of stopping loading.
            if (pendingFirstMessageRef.current && wsRef.current?.readyState === WebSocket.OPEN) {
              const queuedMessage = pendingFirstMessageRef.current;
              pendingFirstMessageRef.current = null;

              // Mark any streaming greeting as complete before sending
              setMessages((prev) => {
                const lastMessage = prev[prev.length - 1];
                if (lastMessage?.role === "assistant" && lastMessage.isStreaming) {
                  return [...prev.slice(0, -1), { ...lastMessage, isStreaming: false }];
                }
                return prev;
              });

              wsRef.current.send(
                JSON.stringify({ type: "message", content: queuedMessage }),
              );
              break;
            }

            setIsLoading(false);
            currentAssistantMessageRef.current = null;

            // Mark current streaming message as complete
            setMessages((prev) => {
              const lastMessage = prev[prev.length - 1];
              if (
                lastMessage?.role === "assistant" &&
                lastMessage.isStreaming
              ) {
                return [
                  ...prev.slice(0, -1),
                  { ...lastMessage, isStreaming: false },
                ];
              }
              return prev;
            });
            break;
          }

          case "error": {
            setIsLoading(false);
            onError?.(data.content);

            setMessages((prev) => [
              ...prev,
              {
                id: generateId(),
                role: "system",
                content: `Error: ${data.content}`,
                timestamp: new Date(),
              },
            ]);
            break;
          }

          case "pong": {
            // Keep-alive response, nothing to do
            break;
          }
        }
      } catch (e) {
        console.error("Failed to parse WebSocket message:", e);
      }
    };
  }, [onError]);

  const start = useCallback(
    (existingConversationId?: number | null, workingDirectory?: string, initialMessage?: string) => {
      // Clear any pending check timeout from a previous call
      if (checkAndSendTimeoutRef.current) {
        clearTimeout(checkAndSendTimeoutRef.current);
        checkAndSendTimeoutRef.current = null;
      }

      // Queue the initial message to be sent after the start handshake completes.
      // The response_done handler will pick this up and send it automatically.
      if (initialMessage) {
        pendingFirstMessageRef.current = initialMessage;
        // Show the user message immediately (optimistic)
        setMessages((prev) => [
          ...prev,
          {
            id: generateId(),
            role: "user" as const,
            content: initialMessage,
            timestamp: new Date(),
          },
        ]);
      }

      connect();

      // Wait for connection then send start message
      const checkAndSend = () => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          checkAndSendTimeoutRef.current = null;
          setIsLoading(true);
          const payload: {
            type: string;
            conversation_id?: number;
            working_directory?: string;
          } = { type: "start" };

          if (existingConversationId) {
            payload.conversation_id = existingConversationId;
            setConversationId(existingConversationId);
          }
          if (workingDirectory) {
            payload.working_directory = workingDirectory;
          }

          if (import.meta.env.DEV) {
            console.debug('[useWorkspaceChat] Sending start message:', payload);
          }
          wsRef.current.send(JSON.stringify(payload));
        } else if (wsRef.current?.readyState === WebSocket.CONNECTING) {
          checkAndSendTimeoutRef.current = window.setTimeout(checkAndSend, 100);
        } else {
          checkAndSendTimeoutRef.current = null;
        }
      };

      checkAndSendTimeoutRef.current = window.setTimeout(checkAndSend, 100);
    },
    [connect],
  );

  const sendMessage = useCallback(
    (content: string) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        onError?.("Not connected");
        return;
      }

      let fullMessage = content;

      // Prepend injection content if present
      if (pendingInjection) {
        const injectedLines = [
          `--- Injected from "${pendingInjection.sourceTitle}" ---`,
          ...pendingInjection.messages.map(
            (m) =>
              `${m.role === "user" ? "User" : "Assistant"}: ${m.content}`,
          ),
          `--- End injection ---`,
          "",
          content,
        ];
        fullMessage = injectedLines.join("\n");
        setPendingInjection(null);
      }

      // Add user message to chat (show original content, not the injected version)
      setMessages((prev) => [
        ...prev,
        {
          id: generateId(),
          role: "user",
          content,
          timestamp: new Date(),
        },
      ]);

      setIsLoading(true);

      wsRef.current.send(
        JSON.stringify({
          type: "message",
          content: fullMessage,
        }),
      );
    },
    [onError, pendingInjection],
  );

  const disconnect = useCallback(() => {
    reconnectAttempts.current = maxReconnectAttempts; // Prevent reconnection
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setConnectionStatus("disconnected");
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setTotalTokens(0);
    setContextBudget({ messageTokens: 0, summaryTokens: 0, messageCount: 0 });
  }, []);

  return {
    messages,
    isLoading,
    connectionStatus,
    conversationId,
    totalTokens,
    contextWindow,
    contextBudget,
    pendingInjection,
    setPendingInjection,
    start,
    sendMessage,
    disconnect,
    clearMessages,
  };
}

/**
 * Generates a user-friendly description for a tool call.
 *
 * Maps tool names to human-readable descriptions, extracting
 * relevant parameters like file paths, search patterns, and
 * command snippets for display in the chat timeline.
 */
function describeToolCall(
  toolName: string,
  input: Record<string, unknown>,
): string {
  switch (toolName) {
    case "Read": {
      const filePath = input.file_path as string | undefined;
      const filename = filePath?.split("/").pop() || filePath || "unknown";
      return `Reading file: ${filename}`;
    }
    case "Write": {
      const filePath = input.file_path as string | undefined;
      const filename = filePath?.split("/").pop() || filePath || "unknown";
      return `Writing file: ${filename}`;
    }
    case "Edit": {
      const filePath = input.file_path as string | undefined;
      const filename = filePath?.split("/").pop() || filePath || "unknown";
      return `Editing file: ${filename}`;
    }
    case "Bash": {
      const command = input.command as string | undefined;
      const cmd = command
        ? command.length > 60
          ? command.substring(0, 60) + "..."
          : command
        : "...";
      return `Running: ${cmd}`;
    }
    case "Glob": {
      const pattern = input.pattern as string | undefined;
      return `Searching for files: ${pattern || "..."}`;
    }
    case "Grep": {
      const pattern = input.pattern as string | undefined;
      return `Searching for: ${pattern || "..."}`;
    }
    case "WebFetch": {
      return "Fetching web content";
    }
    case "WebSearch": {
      const query = input.query as string | undefined;
      return `Searching web: ${query || "..."}`;
    }
    default: {
      return `Using tool: ${toolName}`;
    }
  }
}
