import { useState, useRef, useEffect } from 'react';
import ChatPanel from './components/ChatPanel';
import StarChartPanel from './components/StarChartPanel';
import { useChatStream } from './hooks/useChatStream';

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

function ConstellationBg() {
  return (
    <svg className="fixed inset-0 pointer-events-none opacity-[0.03]" aria-hidden="true">
      <defs>
        <radialGradient id="star-glow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#6366f1" />
          <stop offset="100%" stopColor="transparent" />
        </radialGradient>
      </defs>
      {[
        { cx: '15%', cy: '20%', r: 120 }, { cx: '72%', cy: '15%', r: 80 },
        { cx: '45%', cy: '60%', r: 150 }, { cx: '85%', cy: '70%', r: 100 },
        { cx: '25%', cy: '80%', r: 90 },  { cx: '60%', cy: '35%', r: 70 },
        { cx: '90%', cy: '45%', r: 110 }, { cx: '10%', cy: '55%', r: 60 },
      ].map((dot, i) => (
        <circle key={i} cx={dot.cx} cy={dot.cy} r="2" fill="#6366f1" opacity="0.5" />
      ))}
      {[
        ['15%', '20%', '72%', '15%'], ['45%', '60%', '85%', '70%'],
        ['25%', '80%', '60%', '35%'], ['72%', '15%', '45%', '60%'],
      ].map((line, i) => (
        <line key={i} x1={line[0]} y1={line[1]} x2={line[2]} y2={line[3]} stroke="#6366f1" strokeWidth="0.4" opacity="0.4" />
      ))}
    </svg>
  );
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionId, setSessionId] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { stream } = useChatStream();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (question: string) => {
    if (loading || !question.trim()) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: question,
    };

    const assistantMsg: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setLoading(true);

    await stream(question, sessionId, {
      onToken: (token: string) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsg.id
              ? { ...m, content: m.content + token }
              : m
          )
        );
      },
      onSources: (sources: SourceRef[]) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsg.id ? { ...m, sources } : m
          )
        );
      },
      onSession: (sid: string) => {
        if (sid && !sessionId) {
          setSessionId(sid);
        }
      },
      onDone: () => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsg.id ? { ...m, isStreaming: false } : m
          )
        );
        setLoading(false);
      },
      onError: (error: Error) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsg.id
              ? {
                  ...m,
                  content: m.content
                    ? m.content + `\n\n---\n⚠️ 请求出错: ${error.message}`
                    : `⚠️ 请求出错: ${error.message}`,
                  isStreaming: false,
                }
              : m
          )
        );
        setLoading(false);
      },
    });
  };

  const handleClear = async () => {
    if (sessionId) {
      await fetch(`/api/chat/${sessionId}`, { method: 'DELETE' });
    }
    setMessages([]);
    setSessionId('');
  };

  return (
    <div className="flex flex-col h-screen bg-gray-950 relative">
      <ConstellationBg />

      <header className="flex items-center justify-between px-6 py-3 border-b border-gray-800/60 bg-gray-900/40 backdrop-blur-sm relative z-10">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-indigo-500/15 border border-indigo-500/25 flex items-center justify-center text-lg">
            🔭
          </div>
          <div>
            <h1 className="text-base font-semibold text-gray-100 tracking-tight">AstroRAG</h1>
            <p className="text-[11px] text-gray-500">天文知识智能问答</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {sessionId && (
            <span className="text-[10px] text-gray-600 font-mono bg-gray-900 px-2 py-1 rounded-md border border-gray-800/50">
              {sessionId.slice(0, 8)}...
            </span>
          )}
          <button
            onClick={handleClear}
            className="px-3 py-1.5 text-xs text-gray-400 hover:text-gray-200 bg-gray-800/60 hover:bg-gray-700/80 rounded-lg transition-all border border-gray-700/30 hover:border-gray-600/50"
          >
            新对话
          </button>
        </div>
      </header>

      <main className="grid min-h-0 flex-1 grid-rows-[minmax(0,1fr)_minmax(560px,42vh)] overflow-hidden lg:grid-cols-[minmax(0,1fr)_minmax(390px,44vw)] lg:grid-rows-1 relative z-10">
        <section className="min-h-0 min-w-0">
          <ChatPanel
            messages={messages}
            loading={loading}
            onSend={handleSend}
            messagesEndRef={messagesEndRef}
          />
        </section>
        <StarChartPanel />
      </main>

      <footer className="px-6 py-2 text-center text-[10px] text-gray-700 border-t border-gray-800/40 relative z-10">
        Powered by LM Studio 本地推理 · BGE-M3 + ChromaDB · 梅西耶 / NGC/IC / 星座与天文术语
      </footer>
    </div>
  );
}

export default App;
