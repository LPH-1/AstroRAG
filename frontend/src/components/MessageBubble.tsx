import { useState, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import rehypeRaw from 'rehype-raw';

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

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    });
  }, [text]);

  return (
    <button
      onClick={handleCopy}
      className="absolute top-2 right-2 px-2 py-1 text-xs rounded bg-gray-700/60 text-gray-400 hover:bg-gray-600 hover:text-gray-200 opacity-0 group-hover:opacity-100 transition-all"
    >
      {copied ? '已复制' : '复制'}
    </button>
  );
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const [showSources, setShowSources] = useState(false);
  const isUser = message.role === 'user';

  const markdownComponents = {
    h1: ({ children, ...props }: React.ComponentPropsWithoutRef<'h1'>) => (
      <h1 className="text-xl font-bold text-indigo-300 mt-4 mb-2 first:mt-1 border-b border-gray-700/50 pb-1" {...props}>{children}</h1>
    ),
    h2: ({ children, ...props }: React.ComponentPropsWithoutRef<'h2'>) => (
      <h2 className="text-lg font-semibold text-indigo-300/90 mt-3 mb-2 first:mt-1" {...props}>{children}</h2>
    ),
    h3: ({ children, ...props }: React.ComponentPropsWithoutRef<'h3'>) => (
      <h3 className="text-base font-semibold text-gray-200 mt-2 mb-1" {...props}>{children}</h3>
    ),
    p: ({ children, ...props }: React.ComponentPropsWithoutRef<'p'>) => (
      <p className="mb-2 leading-relaxed" {...props}>{children}</p>
    ),
    strong: ({ children, ...props }: React.ComponentPropsWithoutRef<'strong'>) => (
      <strong className="text-amber-300 font-semibold" {...props}>{children}</strong>
    ),
    em: ({ children, ...props }: React.ComponentPropsWithoutRef<'em'>) => (
      <em className="text-gray-300 italic" {...props}>{children}</em>
    ),
    del: ({ children, ...props }: React.ComponentPropsWithoutRef<'del'>) => (
      <del className="text-gray-500 line-through" {...props}>{children}</del>
    ),
    code: ({ className, children, inline, ...props }: React.ComponentPropsWithoutRef<'code'> & { inline?: boolean }) => {
      const match = /language-(\w+)/.exec(className || '');
      const isInline = inline || !match;
      if (isInline) {
        return (
          <code className="bg-gray-700/80 px-1.5 py-0.5 rounded text-emerald-300 text-xs font-mono" {...props}>
            {children}
          </code>
        );
      }
      const codeText = String(children).replace(/\n$/, '');
      return (
        <div className="group relative my-2">
          <CopyButton text={codeText} />
          <pre className="bg-gray-900/80 rounded-lg border border-gray-700/50 overflow-x-auto">
            <code className={`text-sm leading-relaxed p-3 block ${className || ''}`} {...props}>
              {children}
            </code>
          </pre>
        </div>
      );
    },
    pre: ({ children, ...props }: React.ComponentPropsWithoutRef<'pre'>) => (
      <pre className="bg-gray-900/80 rounded-lg border border-gray-700/50 overflow-x-auto my-2" {...props}>{children}</pre>
    ),
    table: ({ children, ...props }: React.ComponentPropsWithoutRef<'table'>) => (
      <div className="overflow-x-auto my-3">
        <table className="min-w-full text-sm border-collapse border border-gray-700/60 rounded-lg overflow-hidden" {...props}>{children}</table>
      </div>
    ),
    thead: ({ children, ...props }: React.ComponentPropsWithoutRef<'thead'>) => (
      <thead className="bg-gray-800/80" {...props}>{children}</thead>
    ),
    th: ({ children, ...props }: React.ComponentPropsWithoutRef<'th'>) => (
      <th className="border border-gray-700/60 px-3 py-2 text-left text-xs font-semibold text-gray-300 uppercase tracking-wider" {...props}>{children}</th>
    ),
    td: ({ children, ...props }: React.ComponentPropsWithoutRef<'td'>) => (
      <td className="border border-gray-700/60 px-3 py-1.5 text-gray-300" {...props}>{children}</td>
    ),
    ul: ({ children, ...props }: React.ComponentPropsWithoutRef<'ul'>) => (
      <ul className="list-disc list-inside mb-2 space-y-0.5 marker:text-indigo-400" {...props}>{children}</ul>
    ),
    ol: ({ children, ...props }: React.ComponentPropsWithoutRef<'ol'>) => (
      <ol className="list-decimal list-inside mb-2 space-y-0.5 marker:text-indigo-400" {...props}>{children}</ol>
    ),
    li: ({ children, ...props }: React.ComponentPropsWithoutRef<'li'>) => (
      <li className="text-gray-200 pl-1" {...props}>{children}</li>
    ),
    blockquote: ({ children, ...props }: React.ComponentPropsWithoutRef<'blockquote'>) => (
      <blockquote className="border-l-3 border-indigo-500/70 pl-4 my-3 py-1 text-gray-400 italic bg-indigo-500/5 rounded-r-lg" {...props}>{children}</blockquote>
    ),
    a: ({ href, children, ...props }: React.ComponentPropsWithoutRef<'a'>) => (
      <a href={href} target="_blank" rel="noopener noreferrer" className="text-indigo-400 underline hover:text-indigo-300 transition-colors" {...props}>{children}</a>
    ),
    hr: (props: React.ComponentPropsWithoutRef<'hr'>) => <hr className="border-gray-700/60 my-4" {...props} />,
    img: ({ src, alt, ...props }: React.ComponentPropsWithoutRef<'img'>) => (
      <img src={src} alt={alt} className="rounded-lg my-2 max-w-full border border-gray-700/40" loading="lazy" {...props} />
    ),
    input: ({ checked, ...props }: React.ComponentPropsWithoutRef<'input'>) => (
      <input type="checkbox" checked={checked} readOnly className="mr-1.5 accent-indigo-500" {...props} />
    ),
  };

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
                  remarkPlugins={[remarkGfm]}
                  rehypePlugins={[rehypeHighlight, rehypeRaw]}
                  components={markdownComponents}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-gray-500">
                <span className="inline-block w-2 h-2 bg-indigo-400 rounded-full animate-pulse" />
                <span className="inline-block w-2 h-2 bg-indigo-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
                <span className="inline-block w-2 h-2 bg-indigo-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }} />
              </div>
            )}

            {message.sources && message.sources.length > 0 && !message.isStreaming && (
              <div className="mt-3 pt-3 border-t border-gray-700/60">
                <button
                  onClick={() => setShowSources(!showSources)}
                  className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors flex items-center gap-1"
                >
                  <span className={`inline-block transition-transform ${showSources ? 'rotate-90' : ''}`}>▸</span>
                  {showSources ? '收起参考来源' : `参考来源 (${message.sources.length})`}
                </button>
                {showSources && (
                  <div className="mt-2 space-y-2 animate-fadeIn">
                    {message.sources.map((src, i) => (
                      <div key={i} className="bg-gray-900/80 rounded-lg px-3 py-2 text-xs border border-gray-700/40">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-amber-400 font-medium">{src.title}</span>
                          <span className="text-gray-600 bg-gray-800 px-1.5 py-0.5 rounded-full text-[10px]">
                            相关度: {(src.score * 100).toFixed(0)}%
                          </span>
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
