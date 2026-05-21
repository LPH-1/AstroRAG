import { useState, useRef, KeyboardEvent } from 'react';
import MessageBubble from './MessageBubble';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: SourceRef[];
  isStreaming?: boolean;
}

interface SourceRef {
  title: string;
  content: string;
  score: number;
}

interface ChatPanelProps {
  messages: Message[];
  loading: boolean;
  onSend: (question: string) => void;
  messagesEndRef: React.LegacyRef<HTMLDivElement>;
}

export default function ChatPanel({ messages, loading, onSend, messagesEndRef }: ChatPanelProps) {
  const [input, setInput] = useState('');
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (!input.trim() || loading) return;
    onSend(input.trim());
    setInput('');
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto px-4 py-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-600">
            <span className="text-6xl mb-6">🌌</span>
            <p className="text-lg text-gray-500 mb-2">探索宇宙的奥秘</p>
            <p className="text-sm text-gray-700 max-w-md text-center">
              试试问：
              «M31是什么？» ·
              «猎户座有哪些梅西耶天体？» ·
              «什么是黑洞？» ·
              «春季适合观测哪些星系？»
            </p>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto space-y-4">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            {loading && !messages[messages.length - 1]?.isStreaming && (
              <div className="flex items-center gap-2 text-gray-500 px-4">
                <span className="inline-block w-2 h-2 bg-indigo-400 rounded-full animate-pulse" />
                <span className="inline-block w-2 h-2 bg-indigo-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
                <span className="inline-block w-2 h-2 bg-indigo-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }} />
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      <div className="border-t border-gray-800 px-4 py-4">
        <div className="max-w-3xl mx-auto flex gap-3 items-end">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入天文问题... (Enter 发送, Shift+Enter 换行)"
            rows={1}
            className="flex-1 bg-gray-800 text-gray-100 rounded-xl px-4 py-3 resize-none outline-none focus:ring-2 focus:ring-indigo-500 placeholder-gray-500 text-sm"
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="px-5 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-xl transition-colors text-sm font-medium"
          >
            {loading ? '...' : '发送'}
          </button>
        </div>
      </div>
    </div>
  );
}
