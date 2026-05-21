import { useState } from 'react';
import ReactMarkdown from 'react-markdown';

interface SourceRef {
  title: string;
  content: string;
  score: number;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: SourceRef[];
  isStreaming?: boolean;
}

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const [showSources, setShowSources] = useState(false);
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={isUser ? 'message-bubble-user' : 'message-bubble-assistant'}>
        {isUser ? (
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="text-sm">
            {message.content ? (
              <div className={message.isStreaming ? 'streaming-cursor' : ''}>
                <ReactMarkdown
                  components={{
                    h1: ({ children }) => <h1 className="text-lg font-bold text-indigo-300 mt-3 mb-1">{children}</h1>,
                    h2: ({ children }) => <h2 className="text-base font-semibold text-indigo-300 mt-2 mb-1">{children}</h2>,
                    h3: ({ children }) => <h3 className="text-sm font-semibold text-gray-200 mt-2 mb-1">{children}</h3>,
                    p: ({ children }) => <p className="mb-2 leading-relaxed">{children}</p>,
                    strong: ({ children }) => <strong className="text-amber-300 font-semibold">{children}</strong>,
                    code: ({ children }) => <code className="bg-gray-700 px-1.5 py-0.5 rounded text-emerald-300 text-xs">{children}</code>,
                    ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
                    ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
                    li: ({ children }) => <li className="text-gray-200">{children}</li>,
                    blockquote: ({ children }) => <blockquote className="border-l-2 border-indigo-500 pl-3 my-2 text-gray-400 italic">{children}</blockquote>,
                    a: ({ href, children }) => <a href={href} target="_blank" rel="noopener noreferrer" className="text-indigo-400 underline">{children}</a>,
                    hr: () => <hr className="border-gray-700 my-3" />,
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
            ) : (
              <span className="text-gray-500 italic">思考中...</span>
            )}

            {message.sources && message.sources.length > 0 && (
              <div className="mt-3 pt-3 border-t border-gray-700">
                <button
                  onClick={() => setShowSources(!showSources)}
                  className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
                >
                  {showSources ? '收起参考来源 ▲' : `参考来源 (${message.sources.length}) ▼`}
                </button>
                {showSources && (
                  <div className="mt-2 space-y-2">
                    {message.sources.map((src, i) => (
                      <div key={i} className="bg-gray-900 rounded-lg px-3 py-2 text-xs">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-amber-400 font-medium">{src.title}</span>
                          <span className="text-gray-600">相关度: {(src.score * 100).toFixed(0)}%</span>
                        </div>
                        <p className="text-gray-400 leading-relaxed line-clamp-3">{src.content}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
