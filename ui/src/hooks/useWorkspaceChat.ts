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
  /** The background session ID this viewer is attached to (null if none). */
  attachedSessionId: string | null;
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

  // Background session viewer protocol state
  const [attachedSessionId, setAttachedSessionId] = useState<string | null>(null);
  const lastSeqRef = useRef<number>(0);
  const attachedSessionIdRef = useRef<string | null>(null);
  // Keep ref in sync with state for use in callbacks
  attachedSessionIdRef.current = attachedSessionId;

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
  const checkAndSendTimeoutRef = useRef<number | null>(null);
  const loadingSafetyTimeoutRef = useRef<number | null>(null);

  // Store the last "start" params so we can re-send on reconnect.
  // Without this, auto-reconnect creates a bare WebSocket with no server session.
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
  const sessionReadyRef = useRef(false);
  // Queue the WebSocket payload to be sent once the session becomes ready.
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
      if (wsRef.current) {
        wsRef.current.close();
      }
      currentAssistantMessageRef.current = null;
      sessionReadyRef.current = false;
      queuedPayloadRef.current = null;
    };
  }, []);

  // Hydrate token log from the database when conversationId changes.
  // This ensures historical token logs persist across page reloads.
  useEffect(() => {
    if (conversationId == null) return;
    let cancelled = false;
    getTokenLog(conversationId)
      .then((entries) => {
        if (cancelled) return;
        if (entries.length > 0) {
          // Merge with any entries already received via WebSocket.
          // Use entry IDs to deduplicate (WebSocket entries may overlap
          // with database entries if the fetch races with streaming).
          setTokenLog((prev) => {
            const existingIds = new Set(prev.map((e) => e.id));
            const newEntries = entries.filter((e) => !existingIds.has(e.id));
            if (newEntries.length === 0) return prev;
            // Combine and sort by id (chronological order)
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
    // If an existing WebSocket is still open or connecting, close it first.
    // Previously this silently returned, which caused zombie connections when
    // disconnect()'s async onclose handler scheduled a reconnect that raced
    // with a new start() call.
    if (wsRef.current) {
      if (
        wsRef.current.readyState === WebSocket.OPEN ||
        wsRef.current.readyState === WebSocket.CONNECTING
      ) {
        // Prevent the closing socket's onclose from scheduling yet another reconnect
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
      setConnectionStatus("connected");
      setLastError(null);
      const wasReconnect = reconnectAttempts.current > 0;
      reconnectAttempts.current = 0;

      // Start ping interval to keep the connection alive
      pingIntervalRef.current = window.setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "ping" }));
        }
      }, 30000);

      // On reconnect, reattach to the existing background session if we
      // have one (viewer protocol). Otherwise fall back to re-sending "start".
      if (wasReconnect) {
        if (attachedSessionIdRef.current) {
          // Reattach to existing background session with catch-up
          const attachPayload = {
            type: "attach",
            session_id: attachedSessionIdRef.current,
            since_seq: lastSeqRef.current,
          };
          if (import.meta.env.DEV) {
            console.debug('[useWorkspaceChat] Reattaching to session on reconnect:', attachPayload);
          }
          ws.send(JSON.stringify(attachPayload));
        } else if (lastStartParamsRef.current) {
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

          if (import.meta.env.DEV) {
            console.debug('[useWorkspaceChat] Re-sending start on reconnect:', payload);
          }
          ws.send(JSON.stringify(payload));
        }
      }
    };

    ws.onclose = (event) => {
      setConnectionStatus("disconnected");
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = null;
      }

      // Capture close reason for display on the Connection Failed screen
      if (event.code !== 1000 && event.code !== 1001) {
        const reason = event.reason
          || (event.code === 1006
            ? "Server connection dropped unexpectedly. The workspace server may have crashed or be rate-limited."
            : `WebSocket closed (code ${event.code})`);
        setLastError(reason);
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
      setLastError("Could not connect to the workspace server. Check that the server is running.");
      onError?.("WebSocket connection error");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WorkspaceChatServerMessage;
        if (import.meta.env.DEV) {
          console.debug('[useWorkspaceChat] Received WebSocket message:', data.type, data);
        }

        // Track sequence number from background session events
        const eventSeq = (data as unknown as Record<string, unknown>).seq as number | undefined;
        if (eventSeq && eventSeq > lastSeqRef.current) {
          lastSeqRef.current = eventSeq;
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
            const tokenData = data as {
              total_tokens: number;
              context_window: number;
              message_count?: number;
              model_id?: string;
              api_input_tokens?: number;
              api_output_tokens?: number;
              api_cache_read_tokens?: number;
              api_cache_creation_tokens?: number;
              cost_usd?: number;
            };
            setTotalTokens(tokenData.total_tokens);
            setContextWindow(tokenData.context_window);
            if (tokenData.model_id) setModelId(tokenData.model_id);
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
            // Branch auto-created for this conversation; the header's
            // branch indicator will refresh automatically via its API call.
            break;
          }

          case "response_done": {
            currentAssistantMessageRef.current = null;
            sessionReadyRef.current = true;

            // Clear walkie-talkie waiting state when response completes
            setAgentWaiting(false);
            setAgentWaitingQuestion(null);

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

            // Dispatch any message that was queued while waiting for session readiness
            if (queuedPayloadRef.current && wsRef.current?.readyState === WebSocket.OPEN) {
              const queued = queuedPayloadRef.current;
              queuedPayloadRef.current = null;
              // Keep isLoading true since we're immediately sending the queued message
              wsRef.current.send(JSON.stringify(queued));
            } else {
              setIsLoading(false);
            }
            break;
          }

          case "rate_limit_logged": {
            // Backend auto-detected a rate limit and logged it
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
            // Informational status from backend (e.g. "Waiting for Opus...")
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
            // Agent output a [WAITING] tag and is waiting for user input.
            // Activate the countdown timer bar and show the question.
            const waitData = data as { question: string };
            const question = waitData.question || "Agent is waiting for your input...";
            setAgentWaiting(true);
            setAgentWaitingQuestion(question);
            addWalkieTalkieEntry('agent', question);
            break;
          }

          case "walkie_talkie_queued": {
            // Confirmation that the walkie-talkie message was queued for the agent.
            // Reset the waiting state since user has responded.
            setAgentWaiting(false);
            setAgentWaitingQuestion(null);
            addWalkieTalkieEntry('system', 'Message delivered to agent');
            break;
          }

          case "token_log": {
            // Real-time token processing log entry from the backend.
            // Append to the log for display in the TokenLogPanel.
            const logData = data as { entry: TokenLogEntry };
            if (logData.entry) {
              setTokenLog((prev) => [...prev, logData.entry]);
            }
            break;
          }

          // --- Background session viewer protocol messages ---

          case "session_created": {
            const scData = data as { session_id: string; conversation_id: number };
            setAttachedSessionId(scData.session_id);
            lastSeqRef.current = 0;
            if (scData.conversation_id) {
              setConversationId(scData.conversation_id);
            }
            break;
          }

          case "replay": {
            // Process replayed events (same handlers as live events).
            // Events arrive as an array with seq numbers.
            const replayData = data as { events: Array<Record<string, unknown>> };
            if (replayData.events) {
              for (const event of replayData.events) {
                const seq = (event.seq ?? event._seq ?? 0) as number;
                if (seq > lastSeqRef.current) {
                  lastSeqRef.current = seq;
                }
                // Replay events flow through the same handlers as live events.
                // We dispatch them as synthetic onmessage calls.
                const eventType = event.type as string;
                if (eventType === "text") {
                  setMessages((prev) => {
                    const lastMessage = prev[prev.length - 1];
                    if (lastMessage?.role === "assistant" && lastMessage.isStreaming) {
                      return [
                        ...prev.slice(0, -1),
                        { ...lastMessage, content: lastMessage.content + (event.content as string || "") },
                      ];
                    } else {
                      return [
                        ...prev,
                        {
                          id: generateId(),
                          role: "assistant",
                          content: (event.content as string) || "",
                          timestamp: new Date(),
                          isStreaming: true,
                        },
                      ];
                    }
                  });
                } else if (eventType === "tool_call") {
                  const toolDesc = describeToolCall(
                    event.tool as string,
                    (event.input as Record<string, unknown>) || {},
                  );
                  setMessages((prev) => [
                    ...prev,
                    { id: generateId(), role: "system", content: toolDesc, timestamp: new Date() },
                  ]);
                } else if (eventType === "response_done") {
                  setMessages((prev) => {
                    const lastMessage = prev[prev.length - 1];
                    if (lastMessage?.role === "assistant" && lastMessage.isStreaming) {
                      return [...prev.slice(0, -1), { ...lastMessage, isStreaming: false }];
                    }
                    return prev;
                  });
                } else if (eventType === "conversation_created") {
                  setConversationId(event.conversation_id as number);
                } else if (eventType === "token_usage") {
                  setTotalTokens((event.total_tokens as number) || 0);
                  setContextWindow((event.context_window as number) || 200_000);
                } else if (eventType === "user_message") {
                  setMessages((prev) => [
                    ...prev,
                    {
                      id: generateId(),
                      role: "user",
                      content: (event.content as string) || "",
                      timestamp: new Date(),
                    },
                  ]);
                }
              }
            }
            break;
          }

          case "replay_done": {
            const rdData = data as { current_seq: number; state: string };
            lastSeqRef.current = rdData.current_seq;
            // Mark streaming messages as complete after replay
            setMessages((prev) => {
              const lastMessage = prev[prev.length - 1];
              if (lastMessage?.role === "assistant" && lastMessage.isStreaming) {
                return [...prev.slice(0, -1), { ...lastMessage, isStreaming: false }];
              }
              return prev;
            });
            // If the session is in a waiting state, mark as ready for input
            if (rdData.state === "waiting_input" || rdData.state === "completed" || rdData.state === "failed") {
              setIsLoading(false);
              sessionReadyRef.current = true;
            }
            break;
          }

          case "heartbeat": {
            const hbData = data as { seq: number };
            if (hbData.seq) {
              lastSeqRef.current = hbData.seq;
            }
            break;
          }

          case "session_state": {
            const ssData = data as { state: string; seq?: number };
            if (ssData.seq && ssData.seq > lastSeqRef.current) {
              lastSeqRef.current = ssData.seq;
            }
            if (ssData.state === "waiting_input") {
              setIsLoading(false);
              sessionReadyRef.current = true;
            } else if (ssData.state === "streaming") {
              setIsLoading(true);
              sessionReadyRef.current = false;
            } else if (ssData.state === "completed") {
              setIsLoading(false);
              sessionReadyRef.current = true;
            } else if (ssData.state === "failed") {
              setIsLoading(false);
              sessionReadyRef.current = true;
            }
            break;
          }

          case "session_completed": {
            setIsLoading(false);
            sessionReadyRef.current = true;
            break;
          }

          case "session_failed": {
            const sfData = data as { error: string };
            setIsLoading(false);
            sessionReadyRef.current = true;
            setMessages((prev) => [
              ...prev,
              {
                id: `fail-${Date.now()}`,
                role: "system",
                content: `Session failed: ${sfData.error || "Unknown error"}`,
                timestamp: new Date(),
              },
            ]);
            break;
          }

          case "session_cancelled": {
            setIsLoading(false);
            sessionReadyRef.current = true;
            setMessages((prev) => [
              ...prev,
              {
                id: `cancel-${Date.now()}`,
                role: "system",
                content: "Session was cancelled.",
                timestamp: new Date(),
              },
            ]);
            break;
          }

          case "detached": {
            // Confirmation that we detached from the session
            break;
          }

          case "error": {
            setIsLoading(false);
            // Mark session as ready so subsequent messages aren't queued
            // into a black hole waiting for a response_done that never comes.
            sessionReadyRef.current = true;
            setLastError(data.content || "Unknown error");
            onError?.(data.content);

            // Check if this is a rate limit or billing error -- auto-log via API as fallback
            const errorContent = (data.content || "").toLowerCase();
            const rateLimitPatterns = [
              "rate limit", "rate_limit", "ratelimit",
              "usage limit", "too many requests", "429",
              "please wait", "try again", "resume at",
              "capacity", "overloaded",
              "credit balance", "balance too low",
              "insufficient credit", "billing",
            ];
            const isRateLimit = rateLimitPatterns.some((p) => errorContent.includes(p));
            const isBillingError = ["credit balance", "balance too low", "insufficient credit"].some(
              (p) => errorContent.includes(p),
            );

            setMessages((prev) => [
              ...prev,
              {
                id: generateId(),
                role: "system",
                content: isBillingError
                  ? `API billing error: ${data.content}\n\nYour API credit balance may be depleted. Top up at console.anthropic.com or switch to 200K mode to use your subscription.`
                  : isRateLimit
                    ? `Rate limit hit! ${data.content}\n\nThis has been auto-logged to calibrate your usage meters.`
                    : `Error: ${data.content}`,
                timestamp: new Date(),
              },
            ]);

            // Frontend fallback: if backend didn't catch it, log via REST
            if (isRateLimit) {
              import("@/lib/api").then(({ logRateLimit: logRL }) => {
                logRL("daily", `Frontend auto-detected: ${data.content?.slice(0, 200)}`).catch(() => {});
              });
            }
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
  }, [onError, addWalkieTalkieEntry]);

  const start = useCallback(
    (existingConversationId?: number | null, workingDirectory?: string, contextMode?: string, costSettings?: Record<string, unknown>, model?: string, provider?: string) => {
      // Clear any pending check timeout from a previous call
      if (checkAndSendTimeoutRef.current) {
        clearTimeout(checkAndSendTimeoutRef.current);
        checkAndSendTimeoutRef.current = null;
      }

      // Clear any pending reconnect from a previous session's onclose handler.
      // Without this, a zombie reconnect can race with this new connection.
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      // Reset reconnect counter so this fresh start() gets full retry budget.
      // (disconnect() deliberately leaves it at maxReconnectAttempts to prevent
      //  the closing socket's onclose from scheduling zombie reconnects.)
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

      // Reset session readiness — the session is not ready until we receive
      // the first response_done after the "start" message is processed.
      sessionReadyRef.current = false;
      queuedPayloadRef.current = null;

      connect();

      // Wait for connection then send start message, with timeout protection
      let checkAttempts = 0;
      const maxCheckAttempts = 100; // 10 seconds max (100 * 100ms)

      const checkAndSend = () => {
        checkAttempts++;
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          checkAndSendTimeoutRef.current = null;
          setIsLoading(true);
          const payload: {
            type: string;
            conversation_id?: number;
            working_directory?: string;
            context_mode?: string;
            cost_settings?: Record<string, unknown>;
            model?: string;
            provider?: string;
          } = { type: "start" };

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

          if (import.meta.env.DEV) {
            console.debug('[useWorkspaceChat] Sending start message:', payload);
          }
          wsRef.current.send(JSON.stringify(payload));
        } else if (
          wsRef.current?.readyState === WebSocket.CONNECTING &&
          checkAttempts < maxCheckAttempts
        ) {
          checkAndSendTimeoutRef.current = window.setTimeout(checkAndSend, 100);
        } else {
          // Connection failed or timed out
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

      // Add user message to chat immediately (show original content, not the injected version)
      // Include attachments so they render inline in the message bubble
      setMessages((prev) => [
        ...prev,
        {
          id: generateId(),
          role: "user",
          content,
          attachments,
          timestamp: new Date(),
        },
      ]);

      setIsLoading(true);

      // Build WebSocket payload with optional attachments
      const wsPayload: Record<string, unknown> = {
        type: "message",
        content: fullMessage,
      };

      if (attachments && attachments.length > 0) {
        wsPayload.attachments = attachments.map((att) => ({
          filename: att.filename,
          mimeType: att.mimeType,
          base64Data: att.base64Data,
        }));
      }

      if (libraryFileIds && libraryFileIds.length > 0) {
        wsPayload.library_file_ids = libraryFileIds;
      }

      // If the WebSocket isn't open yet or the backend session isn't ready
      // (start still processing), queue the payload to be sent when
      // the session confirms readiness via response_done.
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN || !sessionReadyRef.current) {
        queuedPayloadRef.current = wsPayload;
        return;
      }

      wsRef.current.send(JSON.stringify(wsPayload));
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

  const disconnect = useCallback(() => {
    // Set to max to prevent the closing socket's async onclose from scheduling
    // zombie reconnects. The next start() call resets this to 0.
    reconnectAttempts.current = maxReconnectAttempts;
    lastStartParamsRef.current = null; // Clear so reconnect doesn't re-send stale start
    sessionReadyRef.current = false;
    queuedPayloadRef.current = null;
    // Reset the conversation identity so callers (handleSend) don't think
    // a session is still active for the old conversation.
    setConversationId(null);

    // Send detach before closing so the background session keeps running
    if (wsRef.current?.readyState === WebSocket.OPEN && attachedSessionIdRef.current) {
      try {
        wsRef.current.send(JSON.stringify({ type: "detach" }));
      } catch {
        // Ignore send errors during disconnect
      }
    }
    setAttachedSessionId(null);
    lastSeqRef.current = 0;

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
    // NOTE: Do NOT reset reconnectAttempts here. Leaving it at maxReconnectAttempts
    // ensures the async onclose handler (which fires after this function returns)
    // will NOT schedule a zombie reconnect. The next start() call resets it to 0.
    setConnectionStatus("disconnected");
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setTotalTokens(0);
    setContextBudget({ messageTokens: 0, summaryTokens: 0, messageCount: 0 });
    setAgentWaiting(false);
    setAgentWaitingQuestion(null);
    setWalkieTalkieLog([]);
    setTokenLog([]);
    sessionReadyRef.current = false;
    queuedPayloadRef.current = null;
    setAttachedSessionId(null);
    lastSeqRef.current = 0;
  }, []);

  // Adaptive safety timeout: provider-aware to support long-running sessions.
  // Claude sessions get a 10-minute timeout (fast model, quick responses).
  // Codex/Gemini sessions can run for hours, so they get NO timeout — they
  // rely on the WebSocket ping/pong keepalive and show a non-destructive
  // warning after 30 minutes instead of force-resetting isLoading.
  useEffect(() => {
    if (isLoading) {
      const provider = lastStartParamsRef.current?.provider ?? 'claude';
      const isLongRunningProvider = provider === 'codex' || provider === 'gemini';

      if (isLongRunningProvider) {
        // For Codex/Gemini: show a non-destructive info message after 30 min,
        // but do NOT reset isLoading — the session may still be working.
        loadingSafetyTimeoutRef.current = window.setTimeout(() => {
          setMessages((prev) => {
            // Don't add duplicate long-running notices
            if (prev.some(m => m.id.startsWith('long-running-'))) return prev;
            return [
              ...prev,
              {
                id: `long-running-${Date.now()}`,
                role: "system" as const,
                content: `Session has been running for 30+ minutes. ${provider === 'codex' ? 'Codex' : 'Gemini'} agents can run for hours — the session is still active.`,
                timestamp: new Date(),
              },
            ];
          });
        }, 30 * 60 * 1000);
      } else {
        // For Claude: keep the original 10-minute safety timeout
        loadingSafetyTimeoutRef.current = window.setTimeout(() => {
          setIsLoading(false);
          sessionReadyRef.current = true;
          setMessages((prev) => [
            ...prev,
            {
              id: `safety-${Date.now()}`,
              role: "system" as const,
              content: "Request timed out (10 min). The connection may have dropped. Try sending your message again.",
              timestamp: new Date(),
            },
          ]);
        }, 10 * 60 * 1000);
      }
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
    attachedSessionId,
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
