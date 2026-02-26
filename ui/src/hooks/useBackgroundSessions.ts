/**
 * Hook for polling background session status from the server.
 *
 * Provides real-time awareness of all running background sessions so the
 * sidebar and dashboard can show session status independently of WebSocket
 * connections.
 */

import { useQuery } from '@tanstack/react-query';

export interface BackgroundSessionStatus {
  session_id: string;
  conversation_id: number;
  state: string;
  provider: string;
  model: string;
  working_directory: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  viewer_count: number;
  buffer_sequence: number;
}

export function useBackgroundSessions() {
  return useQuery<BackgroundSessionStatus[]>({
    queryKey: ['background-sessions'],
    queryFn: async () => {
      const res = await fetch('/api/workspace/sessions');
      if (!res.ok) throw new Error('Failed to fetch sessions');
      return res.json();
    },
    refetchInterval: 5000, // Poll every 5 seconds
  });
}
