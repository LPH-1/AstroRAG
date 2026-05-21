import { useCallback, useRef } from 'react';

interface SourceRef {
  title: string;
  content: string;
  score: number;
}

interface StreamCallbacks {
  onToken: (token: string) => void;
  onSources: (sources: SourceRef[]) => void;
  onSession: (sessionId: string) => void;
  onDone: () => void;
  onError: (error: Error) => void;
}

export function useChatStream() {
  const abortRef = useRef<AbortController | null>(null);

  const stream = useCallback(async (question: string, sessionId: string, callbacks: StreamCallbacks) => {
    abortRef.current?.abort();
    abortRef.current = new AbortController();

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, sessionId }),
        signal: abortRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('Response body is not readable');

      const decoder = new TextDecoder();
      let buffer = '';
      let currentEvent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('event:')) {
            currentEvent = line.slice(6).trim();
          } else if (line.startsWith('data:')) {
            const data = line.slice(5).trim();

            try {
              switch (currentEvent) {
                case 'token':
                  callbacks.onToken(data);
                  break;
                case 'sources':
                  callbacks.onSources(JSON.parse(data));
                  break;
                case 'session':
                  callbacks.onSession(data);
                  break;
                case 'done':
                  callbacks.onDone();
                  break;
              }
            } catch {
              // If JSON parse fails, it might be a raw token
              if (currentEvent === 'token' || !currentEvent) {
                callbacks.onToken(data);
              }
            }
            currentEvent = '';
          }
        }
      }
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') {
        return;
      }
      callbacks.onError(error instanceof Error ? error : new Error(String(error)));
    }
  }, []);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  return { stream, cancel };
}
