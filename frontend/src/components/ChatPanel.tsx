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

const SUGGESTIONS = [
  { icon: '🌌', text: 'M31是什么？', desc: '仙女座星系' },
  { icon: '⭐', text: '猎户座有哪些梅西耶天体？', desc: '星座探索' },
  { icon: '🕳️', text: '什么是黑洞？', desc: '天体物理' },
  { icon: '🔭', text: '春季适合观测哪些星系？', desc: '观测指南' },
];

function WelcomeScreen({ onSend, loading }: { onSend: (q: string) => void; loading: boolean }) {
  return (
    <div className="flex flex-col items-center justify-center h-full px-6">
      <div className="animate-fadeInUp text-center max-w-lg">
        <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
          <span className="text-4xl">🌌</span>
        </div>
        <h2 className="text-2xl font-semibold text-gray-100 mb-2 tracking-tight">探索宇宙的奥秘</h2>
        <p className="text-sm text-gray-500 mb-8 leading-relaxed">
          基于 RAG 技术的天文知识问答系统，覆盖梅西耶天体、NGC/IC 星表、星座与天文术语
        </p>
        <div className="grid grid-cols-2 gap-2 w-full max-w-md">
          {SUGGESTIONS.map((s) => (
            <button
              key={s.text}
              onClick={() => !loading && onSend(s.text)}
              disabled={loading}
              className="flex items-start gap-2.5 px-3.5 py-3 rounded-xl bg-gray-800/40 border border-gray-700/30 hover:bg-gray-800 hover:border-gray-600/50 transition-all text-left group disabled:opacity-40"
            >
              <span className="text-lg mt-0.5">{s.icon}</span>
              <div>
                <p className="text-sm text-gray-300 group-hover:text-gray-100 transition-colors">{s.text}</p>
                <p className="text-[10px] text-gray-600 mt-0.5">{s.desc}</p>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
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
          <WelcomeScreen onSend={onSend} loading={loading} />
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

      <div className="border-t border-gray-800/60 px-4 py-4">
        <div className="max-w-3xl mx-auto flex gap-3 items-end">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入天文问题... (Enter 发送, Shift+Enter 换行)"
              rows={1}
              className="w-full bg-gray-800/60 text-gray-100 rounded-xl px-4 py-3 resize-none outline-none focus:ring-2 focus:ring-indigo-500/50 focus:bg-gray-800 placeholder-gray-500 text-sm border border-gray-700/30 focus:border-indigo-500/50 transition-all"
              disabled={loading}
            />
          </div>
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="shrink-0 px-5 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-xl transition-all text-sm font-medium shadow-lg shadow-indigo-500/20 active:scale-95 disabled:shadow-none"
          >
            {loading ? (
              <span className="flex items-center gap-1">
                <span className="inline-block w-1.5 h-1.5 bg-indigo-300 rounded-full animate-pulse" />
                <span className="inline-block w-1.5 h-1.5 bg-indigo-300 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
              </span>
            ) : (
              '发送'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
