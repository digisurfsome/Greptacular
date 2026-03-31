/**
 * Hook for managing workspace chat WebSocket connection.
 *
 * Simplified: one WebSocket, one session per page.  No viewer protocol,
 * no background session manager, no attach/detach/replay.  The session
 * lives and dies with the WebSocket connection.  On reconnect, the
 * frontend sends "start" with the same conversation_id and history
 * is loaded from the database.
 */

import { useState, useCallback, useRef, useEffect } from "react";
import { getTokenLog } from "../lib/api";
import type { ChatMessage, WorkspaceChatServerMessage, PendingInjection, ImageAttachment, WalkieTalkieLogEntry, TokenLogEntry } from "../lib/types";

type ConnectionStatus = "disconnected" | "connecting" | "connected" | "error";

interface UseWorkspaceChatOptions {
  onError?: (error: string) => void;
}

interface UseWorkspaceChatReturn {
  messages: ChatMessage[];
  isLoading: boolean;
  connectionStatus: ConnectionStatus;
  lastError: string | null;
  conversationId: number | null;
  totalTokens: number;
  contextWindow: number;
  contextBudget: {
    messageTokens: number;
    summaryTokens: number;
    messageCount: number;
  };
  /** The resolved model ID reported by the backend (e.g. "claude-opus-4-6"). */
  modelId: string | null;
  pendingInjection: PendingInjection | null;
  setPendingInjection: (injection: PendingInjection | null) => void;
  /** Whether the agent is waiting for user input (output [WAITING] tag). */
  agentWaiting: boolean;
  /** The question the agent asked when entering waiting state. */
  agentWaitingQuestion: string | null;
  start: (conversationId?: number | null, workingDirectory?: string, contextMode?: string, costSettings?: Record<string, unknown>, model?: string, provider?: string) => void;
  sendMessage: (content: string, attachments?: ImageAttachment[], libraryFileIds?: number[]) => void;
  /** Send a walkie-talkie message to the running agent (injected via PreToolUse hook). */
  sendWalkieTalkie: (content: string) => void;
  /** Walkie-talkie conversation log for display in the sidebar panel. */
  walkieTalkieLog: WalkieTalkieLogEntry[];
  /** Append an entry to the walkie-talkie log (used by WorkspaceChat for user-initiated events). */
  addWalkieTalkieEntry: (sender: 'user' | 'agent' | 'system', content: string) => void;
  /** Real-time token processing log entries received via WebSocket. */
  tokenLog: TokenLogEntry[];
  /** Clear the local token log entries array. */
  clearTokenLog: () => void;
  /** Cancel the running session (closes WebSocket, auto-reconnects). */
  cancelSession: () => void;
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
  const [contextWindow, setContextWindow] = useState(200_000);
  const [contextBudget, setContextBudget] = useState<{
    messageTokens: number;
    summaryTokens: number;
    messageCount: number;
  }>({
    messageTokens: 0,
    summaryTokens: 0,
    messageCount: 0,
  });
  const [modelId, setModelId] = useState<string | null>(null);
  const [pendingInjection, setPendingInjection] = useState<PendingInjection | null>(null);
  const [lastError, setLastError] = useState<string | null>(null);
  const [agentWaiting, setAgentWaiting] = useState(false);
  const [agentWaitingQuestion, setAgentWaitingQuestion] = useState<string | null>(null);
  const [walkieTalkieLog, setWalkieTalkieLog] = useState<WalkieTalkieLogEntry[]>([]);
  const [tokenLog, setTokenLog] = useState<TokenLogEntry[]>([]);

  const addWalkieTalkieEntry = useCallback(
    (sender: 'user' | 'agent' | 'system', content: string) => {
      setWalkieTalkieLog((prev) => [
        ...prev,
        {
          id: `wt-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
          sender,
          content,
          timestamp: new Date(),
        },
      ]);
    },
    [],
  );

  const wsRef = useRef<WebSocket | null>(null);
  const currentAssistantMessageRef = useRef<string | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 3;
  const pingIntervalRef = useRef<number | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const connectionGenerationRef = useRef(0);
  const checkAndSendTimeoutRef = useRef<number | null>(null);
  const loadingSafetyTimeoutRef = useRef<number | null>(null);

  // Store the last "start" params so we can re-send on reconnect.
  const lastStartParamsRef = useRef<{
    conversationId?: number;
    workingDirectory?: string;
    contextMode?: string;
    costSettings?: Record<string, unknown>;
    model?: string;
    provider?: string;
  } | null>(null);

  // Session readiness tracking: prevents sending messages before the backend
  // session is fully established (Claude SDK client created, greeting sent).
  // Once the first response_done fires, the session is ready and stays ready
  // — we no longer gate on this per-message (that caused the stuck message bug).
  const sessionReadyRef = useRef(false);
  const queuedPayloadRef = useRef<Record<string, unknown> | null>(null);

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
      if (loadingSafetyTimeoutRef.current) {
        clearTimeout(loadingSafetyTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
      currentAssistantMessageRef.current = null;
      sessionReadyRef.current = false;
      queuedPayloadRef.current = null;
    };
  }, []);

  // Hydrate token log from the database when conversationId changes.
  useEffect(() => {
    if (conversationId == null) return;
    let cancelled = false;
    getTokenLog(conversationId)
      .then((entries) => {
        if (cancelled) return;
        if (entries.length > 0) {
          setTokenLog((prev) => {
            const existingIds = new Set(prev.map((e) => e.id));
            const newEntries = entries.filter((e) => !existingIds.has(e.id));
            if (newEntries.length === 0) return prev;
            return [...newEntries, ...prev].sort(
              (a, b) => (a.id ?? 0) - (b.id ?? 0),
            );
          });
        }
      })
      .catch((err) => {
        if (!cancelled) {
          console.warn("Failed to load historical token log:", err);
        }
      });
    return () => { cancelled = true; };
  }, [conversationId]);

  const connect = useCallback(() => {
    connectionGenerationRef.current++;
    const thisGeneration = connectionGenerationRef.current;

    if (wsRef.current) {
      if (
        wsRef.current.readyState === WebSocket.OPEN ||
        wsRef.current.readyState === WebSocket.CONNECTING
      ) {
        reconnectAttempts.current = maxReconnectAttempts;
        wsRef.current.close();
      }
      wsRef.current = null;
    }

    setConnectionStatus("connecting");

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/api/workspace/ws`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      if (connectionGenerationRef.current !== thisGeneration) {
        ws.close();
        return;
      }
      setConnectionStatus("connected");
      setLastError(null);
      const wasReconnect = reconnectAttempts.current > 0;
      reconnectAttempts.current = 0;

      // Start ping interval
      pingIntervalRef.current = window.setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "ping" }));
        }
      }, 30000);

      // On reconnect, re-send "start" with saved params to resume the conversation.
      if (wasReconnect && lastStartParamsRef.current) {
        sessionReadyRef.current = false;
        const params = lastStartParamsRef.current;
        const payload: Record<string, unknown> = { type: "start" };
        if (params.conversationId != null) {
          payload.conversation_id = params.conversationId;
        }
        if (params.workingDirectory) {
          payload.working_directory = params.workingDirectory;
        }
        payload.context_mode = params.contextMode ?? "200k";
        if (params.costSettings) {
          payload.cost_settings = params.costSettings;
        }
        if (params.model) {
          payload.model = params.model;
        }
        if (params.provider) {
          payload.provider = params.provider;
        }
        ws.send(JSON.stringify(payload));
      }
    };

    ws.onclose = (event) => {
      if (connectionGenerationRef.current !== thisGeneration) {
        return;
      }

      setConnectionStatus("disconnected");
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = null;
      }

      if (event.code !== 1000 && event.code !== 1001) {
        const reason = event.reason
          || (event.code === 1006
            ? "Server connection dropped unexpectedly. The workspace server may have crashed or be rate-limited."
            : `WebSocket closed (code ${event.code})`);
        setLastError(reason);
      }

      // Attempt reconnection with exponential backoff
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
      if (connectionGenerationRef.current !== thisGeneration) return;
      setConnectionStatus("error");
      setLastError("Could not connect to the workspace server. Check that the server is running.");
      onError?.("WebSocket connection error");
    };

    ws.onmessage = (event) => {
      if (connectionGenerationRef.current !== thisGeneration) return;
      try {
        const data = JSON.parse(event.data) as WorkspaceChatServerMessage;
        if (data.type !== 'pong') {
          console.log('[WS]', data.type, data.type === 'token_log' ? (data as unknown as Record<string, unknown>).entry : '');
        }

        switch (data.type) {
          case "text": {
            setMessages((prev) => {
              // Find the streaming assistant message BY ID, not by position.
              // tool_call and status events insert system messages that push
              // the streaming message away from the last position.
              const streamingId = currentAssistantMessageRef.current;
              if (streamingId) {
                const idx = prev.findIndex(m => m.id === streamingId);
                if (idx !== -1) {
                  return [
                    ...prev.slice(0, idx),
                    {
                      ...prev[idx],
                      content: prev[idx].content + data.content,
                    },
                    ...prev.slice(idx + 1),
                  ];
                }
              }
              // No existing streaming message — create a new one
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
            const tokenData = data as {
              total_tokens: number;
              context_window: number;
              message_count?: number;
              model_id?: string;
            };
            setTotalTokens(tokenData.total_tokens);
            setContextWindow(tokenData.context_window);
            if (tokenData.model_id && typeof tokenData.model_id === 'string') setModelId(tokenData.model_id);
            setContextBudget(prev => ({
              ...prev,
              messageTokens: tokenData.total_tokens,
              messageCount: tokenData.message_count ?? prev.messageCount,
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

          case "branch_created": {
            break;
          }

          case "response_done": {
            // Capture the streaming message ID before clearing it
            const doneMessageId = currentAssistantMessageRef.current;
            currentAssistantMessageRef.current = null;
            sessionReadyRef.current = true;

            setAgentWaiting(false);
            setAgentWaitingQuestion(null);

            // Mark the streaming message as complete BY ID, not by position.
            setMessages((prev) => {
              if (!doneMessageId) return prev;
              const idx = prev.findIndex(m => m.id === doneMessageId && m.isStreaming);
              if (idx !== -1) {
                return [
                  ...prev.slice(0, idx),
                  { ...prev[idx], isStreaming: false },
                  ...prev.slice(idx + 1),
                ];
              }
              return prev;
            });

            // Dispatch any message that was queued before the session was ready
            // (i.e., sent before the greeting completed). This only fires once.
            if (queuedPayloadRef.current && wsRef.current?.readyState === WebSocket.OPEN) {
              const queued = queuedPayloadRef.current;
              queuedPayloadRef.current = null;
              setTimeout(() => {
                if (wsRef.current?.readyState === WebSocket.OPEN) {
                  wsRef.current.send(JSON.stringify(queued));
                }
              }, 0);
            }
            setIsLoading(false);
            break;
          }

          case "rate_limit_logged": {
            const rlData = data as { event_type: string; tokens_at_hit: number };
            setMessages((prev) => [
              ...prev,
              {
                id: generateId(),
                role: "system",
                content: `Rate limit detected and logged for calibration (${rlData.event_type}, ${rlData.tokens_at_hit.toLocaleString()} tokens). Meters will update automatically.`,
                timestamp: new Date(),
              },
            ]);
            break;
          }

          case "status": {
            setMessages((prev) => [
              ...prev,
              {
                id: generateId(),
                role: "system",
                content: data.content || "Processing...",
                timestamp: new Date(),
              },
            ]);
            break;
          }

          case "agent_waiting": {
            const waitData = data as { question: string };
            const question = waitData.question || "Agent is waiting for your input...";
            setAgentWaiting(true);
            setAgentWaitingQuestion(question);
            addWalkieTalkieEntry('agent', question);
            break;
          }

          case "walkie_talkie_queued": {
            setAgentWaiting(false);
            setAgentWaitingQuestion(null);
            addWalkieTalkieEntry('system', 'Message delivered to agent');
            break;
          }

          case "token_log": {
            const logData = data as { entry: TokenLogEntry };
            if (logData.entry) {
              setTokenLog((prev) => [...prev, logData.entry]);
            }
            break;
          }

          case "error": {
            setIsLoading(false);
            sessionReadyRef.current = true;
            const safeContent = typeof data.content === 'string'
              ? data.content
              : (data.content ? JSON.stringify(data.content) : "Unknown error");
            setLastError(safeContent);
            onError?.(safeContent);

            const errorContent = safeContent.toLowerCase();
            const isUnknownMsgType = errorContent.includes("unknown message type");
            const rateLimitPatterns = [
              "rate limit", "rate_limit", "ratelimit",
              "usage limit", "too many requests", "429",
              "please wait", "try again", "resume at",
              "capacity", "overloaded",
              "credit balance", "balance too low",
              "insufficient credit", "billing",
            ];
            const isRateLimit = !isUnknownMsgType && rateLimitPatterns.some((p) => errorContent.includes(p));
            const isBillingError = ["credit balance", "balance too low", "insufficient credit"].some(
              (p) => errorContent.includes(p),
            );

            setMessages((prev) => [
              ...prev,
              {
                id: generateId(),
                role: "system",
                content: isBillingError
                  ? `API billing error: ${safeContent}\n\nYour API credit balance may be depleted. Top up at console.anthropic.com or switch to 200K mode to use your subscription.`
                  : isRateLimit
                    ? `Rate limit hit! ${safeContent}\n\nThis has been auto-logged to calibrate your usage meters.`
                    : `Error: ${safeContent}`,
                timestamp: new Date(),
              },
            ]);

            if (isRateLimit) {
              import("@/lib/api").then(({ logRateLimit: logRL }) => {
                logRL("daily", `Frontend auto-detected: ${data.content?.slice(0, 200)}`).catch(() => {});
              });
            }
            break;
          }

          case "pong": {
            break;
          }
        }
      } catch (e) {
        console.error("Failed to parse WebSocket message:", e);
      }
    };
  }, [onError, addWalkieTalkieEntry]);

  const start = useCallback(
    (existingConversationId?: number | null, workingDirectory?: string, contextMode?: string, costSettings?: Record<string, unknown>, model?: string, provider?: string) => {
      if (checkAndSendTimeoutRef.current) {
        clearTimeout(checkAndSendTimeoutRef.current);
        checkAndSendTimeoutRef.current = null;
      }

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      reconnectAttempts.current = 0;

      // Save start params so auto-reconnect can re-send the "start" message
      lastStartParamsRef.current = {
        conversationId: existingConversationId ?? undefined,
        workingDirectory,
        contextMode,
        costSettings,
        model,
        provider,
      };

      sessionReadyRef.current = false;
      queuedPayloadRef.current = null;

      connect();

      let checkAttempts = 0;
      const maxCheckAttempts = 100;

      const checkAndSend = () => {
        checkAttempts++;
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          checkAndSendTimeoutRef.current = null;
          setIsLoading(true);
          const payload: Record<string, unknown> = { type: "start" };

          if (existingConversationId != null) {
            payload.conversation_id = existingConversationId;
            setConversationId(existingConversationId);
          }
          if (workingDirectory) {
            payload.working_directory = workingDirectory;
          }
          payload.context_mode = contextMode ?? "200k";
          if (costSettings) {
            payload.cost_settings = costSettings;
          }
          if (model) {
            payload.model = model;
          }
          if (provider) {
            payload.provider = provider;
          }

          wsRef.current.send(JSON.stringify(payload));
        } else if (
          wsRef.current?.readyState === WebSocket.CONNECTING &&
          checkAttempts < maxCheckAttempts
        ) {
          checkAndSendTimeoutRef.current = window.setTimeout(checkAndSend, 100);
        } else {
          checkAndSendTimeoutRef.current = null;
          if (checkAttempts >= maxCheckAttempts) {
            onError?.("Connection timed out. The workspace server may be unavailable.");
            setConnectionStatus("disconnected");
          }
        }
      };

      checkAndSendTimeoutRef.current = window.setTimeout(checkAndSend, 100);
    },
    [connect, onError],
  );

  const sendMessage = useCallback(
    (content: string, attachments?: ImageAttachment[], libraryFileIds?: number[]) => {
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

      // Add user message to chat immediately
      setMessages((prev) => [
        ...prev,
        {
          id: generateId(),
          role: "user",
          content,
          timestamp: new Date(),
          attachments: attachments ? [...attachments] : undefined,
        },
      ]);

      setIsLoading(true);
      setLastError(null);

      const payload: Record<string, unknown> = {
        type: "message",
        content: fullMessage,
      };
      if (attachments && attachments.length > 0) {
        payload.attachments = attachments.map(a => ({
          filename: a.filename,
          mimeType: a.mimeType,
          base64Data: a.base64Data,
        }));
      }
      if (libraryFileIds && libraryFileIds.length > 0) {
        payload.library_file_ids = libraryFileIds;
      }

      // If session is ready (greeting received), send immediately.
      // Otherwise queue for delivery after the first response_done.
      // NOTE: We no longer set sessionReadyRef=false after each send.
      // That was causing the "stuck message" bug — messages sent while
      // waiting for a response would get queued and only dispatch on
      // the next response_done, creating a "stuck then burst" effect.
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        if (sessionReadyRef.current) {
          wsRef.current.send(JSON.stringify(payload));
        } else {
          // Only queue if session hasn't been established yet (pre-greeting)
          queuedPayloadRef.current = payload;
        }
      } else {
        queuedPayloadRef.current = payload;
      }
    },
    [pendingInjection],
  );

  const sendWalkieTalkie = useCallback(
    (content: string) => {
      if (!content.trim()) return;
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({ type: "walkie_talkie", content: content.trim() }),
        );
      }
    },
    [],
  );

  const cancelSession = useCallback(() => {
    // Close the WebSocket — server cleans up the session.
    // Auto-reconnect will re-send "start" with the same conversationId.
    setIsLoading(false);
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.close();
    }
  }, []);

  const disconnect = useCallback(() => {
    reconnectAttempts.current = maxReconnectAttempts;
    lastStartParamsRef.current = null;
    sessionReadyRef.current = false;
    queuedPayloadRef.current = null;
    setConversationId(null);

    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (checkAndSendTimeoutRef.current) {
      clearTimeout(checkAndSendTimeoutRef.current);
      checkAndSendTimeoutRef.current = null;
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
    setLastError(null);
    setModelId(null);
    setAgentWaiting(false);
    setAgentWaitingQuestion(null);
    setWalkieTalkieLog([]);
    setTokenLog([]);
    sessionReadyRef.current = false;
    queuedPayloadRef.current = null;
  }, []);

  // Safety timeout for long-running sessions
  useEffect(() => {
    if (isLoading) {
      const provider = lastStartParamsRef.current?.provider ?? 'claude';
      loadingSafetyTimeoutRef.current = window.setTimeout(() => {
        setMessages((prev) => {
          if (prev.some(m => m.id.startsWith('long-running-'))) return prev;
          const providerLabel = provider === 'codex' ? 'Codex' : provider === 'gemini' ? 'Gemini' : 'Claude';
          return [
            ...prev,
            {
              id: `long-running-${Date.now()}`,
              role: "system" as const,
              content: `Session has been running for 30+ minutes. ${providerLabel} agents can run for extended periods — the session is still active.`,
              timestamp: new Date(),
            },
          ];
        });
      }, 30 * 60 * 1000);
    } else if (loadingSafetyTimeoutRef.current) {
      window.clearTimeout(loadingSafetyTimeoutRef.current);
      loadingSafetyTimeoutRef.current = null;
    }
    return () => {
      if (loadingSafetyTimeoutRef.current) {
        window.clearTimeout(loadingSafetyTimeoutRef.current);
        loadingSafetyTimeoutRef.current = null;
      }
    };
  }, [isLoading]);

  return {
    messages,
    isLoading,
    connectionStatus,
    lastError,
    conversationId,
    totalTokens,
    contextWindow,
    contextBudget,
    modelId,
    pendingInjection,
    setPendingInjection,
    agentWaiting,
    agentWaitingQuestion,
    walkieTalkieLog,
    addWalkieTalkieEntry,
    start,
    sendMessage,
    sendWalkieTalkie,
    tokenLog,
    clearTokenLog: useCallback(() => setTokenLog([]), []),
    cancelSession,
    disconnect,
    clearMessages,
  };
}

/**
 * Generates a user-friendly description for a tool call.
 */
function describeToolCall(
  toolName: string,
  input: Record<string, unknown>,
): string {
  switch (toolName) {
    case "Read": {
      const filePath = input.file_path as string | undefined;
      if (filePath) {
        const fileName = filePath.split("/").pop() || filePath;
        return `Reading ${fileName}`;
      }
      return "Reading file";
    }
    case "Write": {
      const filePath = input.file_path as string | undefined;
      if (filePath) {
        const fileName = filePath.split("/").pop() || filePath;
        const content = input.content as string | undefined;
        const lineCount = content ? content.split("\n").length : 0;
        return lineCount > 0
          ? `Writing ${fileName} (${lineCount} lines)`
          : `Writing ${fileName}`;
      }
      return "Writing file";
    }
    case "Edit": {
      const filePath = input.file_path as string | undefined;
      if (filePath) {
        const fileName = filePath.split("/").pop() || filePath;
        const oldStr = input.old_string as string | undefined;
        const newStr = input.new_string as string | undefined;
        if (oldStr && newStr) {
          const removedLines = oldStr.split("\n").length;
          const addedLines = newStr.split("\n").length;
          return `Editing ${fileName} (-${removedLines}/+${addedLines} lines)`;
        }
        return `Editing ${fileName}`;
      }
      return "Editing file";
    }
    case "Bash": {
      const command = input.command as string | undefined;
      if (command) {
        const truncated = command.length > 120 ? command.substring(0, 117) + "..." : command;
        return `Running: ${truncated}`;
      }
      return "Running command";
    }
    case "Glob": {
      const pattern = input.pattern as string | undefined;
      return pattern ? `Searching for ${pattern}` : "Searching files";
    }
    case "Grep": {
      const pattern = input.pattern as string | undefined;
      return pattern ? `Searching for "${pattern}"` : "Searching content";
    }
    case "WebFetch": {
      const url = input.url as string | undefined;
      if (url) {
        try {
          const hostname = new URL(url).hostname;
          return `Fetching ${hostname}`;
        } catch {
          return `Fetching URL`;
        }
      }
      return "Fetching web page";
    }
    case "WebSearch": {
      const query = input.query as string | undefined;
      return query ? `Searching: "${query}"` : "Searching the web";
    }
    default:
      return `Using ${toolName}`;
  }
}
