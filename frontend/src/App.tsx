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
                    ? m.content + `\n\n⚠️ 错误: ${error.message}`
                    : `⚠️ 错误: ${error.message}`,
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
    <div className="flex flex-col h-screen bg-gray-950">
      <header className="flex items-center justify-between px-6 py-3 border-b border-gray-800 bg-gray-900/50 backdrop-blur">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🔭</span>
          <div>
            <h1 className="text-lg font-semibold text-gray-100">AstroRAG</h1>
            <p className="text-xs text-gray-500">天文知识问答系统</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {sessionId && (
            <span className="text-xs text-gray-600 font-mono">
              session: {sessionId.slice(0, 8)}...
            </span>
          )}
          <button
            onClick={handleClear}
            className="px-3 py-1.5 text-xs text-gray-400 hover:text-gray-200 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
          >
            新对话
          </button>
        </div>
      </header>

      <main className="grid min-h-0 flex-1 grid-rows-[minmax(0,1fr)_minmax(560px,42vh)] overflow-hidden lg:grid-cols-[minmax(0,1fr)_minmax(390px,44vw)] lg:grid-rows-1">
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

      <footer className="px-6 py-2 text-center text-xs text-gray-600 border-t border-gray-800">
        Powered by Ollama + Qwen2.5-7B · 本地运行 · 数据来源：梅西耶天体表 / NGC/IC星表 / 星座与天文术语
      </footer>
    </div>
  );
}

export default App;
