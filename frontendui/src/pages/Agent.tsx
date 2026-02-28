import { useState, useRef, useEffect } from "react";
import PageShell from "@/components/PageShell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { api, isApiError, ChatResponse } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { Send, Bot, User } from "lucide-react";
import { toast } from "sonner";
import ReactMarkdown from "react-markdown";
import { motion, AnimatePresence } from "framer-motion";

interface Message {
  role: "user" | "assistant";
  content: string;
  intent?: string;
  confidence?: number;
}

export default function AgentPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const branch = useAppStore((s) => s.branch);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const send = async () => {
    const msg = input.trim();
    if (!msg || loading) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: msg }]);
    setLoading(true);
    try {
      // Prepend branch context so the agent can route properly
      const question = branch && branch !== "all"
        ? `[branch: ${branch}] ${msg}`
        : msg;
      const res: ChatResponse = await api.chat({ question });
      setMessages((m) => [...m, { role: "assistant", content: res.answer, intent: res.intent, confidence: res.confidence }]);
    } catch (err) {
      toast.error(isApiError(err));
      setMessages((m) => [...m, { role: "assistant", content: "Sorry, I couldn't reach the backend. Please try again." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageShell className="flex flex-col h-[calc(100vh-3.5rem)]">
      <h1 className="font-syne text-2xl font-bold mb-4">Agent Chat</h1>

      <Card className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="flex-1 flex items-center justify-center h-full text-muted-foreground text-sm">
              Ask the Conut Ops Agent anything about your operations…
            </div>
          )}
          <AnimatePresence>
            {messages.map((m, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex gap-3 ${m.role === "user" ? "justify-end" : "justify-start"}`}
              >
                {m.role === "assistant" && <Bot className="mt-1 h-6 w-6 shrink-0 text-primary" />}
                <div className={`max-w-[80%] rounded-xl px-4 py-3 text-sm ${m.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"}`}>
                  <div className="prose prose-sm max-w-none dark:prose-invert"><ReactMarkdown>{m.content}</ReactMarkdown></div>
                  {m.intent && (
                    <div className="mt-2 text-[10px] text-muted-foreground flex gap-2">
                      <span>Intent: {m.intent}</span>
                      {m.confidence !== undefined && <span>Confidence: {(m.confidence * 100).toFixed(0)}%</span>}
                    </div>
                  )}
                </div>
                {m.role === "user" && <User className="mt-1 h-6 w-6 shrink-0 text-muted-foreground" />}
              </motion.div>
            ))}
          </AnimatePresence>
          {loading && (
            <div className="flex gap-3">
              <Bot className="mt-1 h-6 w-6 text-primary" />
              <div className="bg-muted rounded-xl px-4 py-3">
                <div className="flex gap-1">
                  <span className="h-2 w-2 rounded-full bg-primary animate-bounce [animation-delay:0ms]" />
                  <span className="h-2 w-2 rounded-full bg-primary animate-bounce [animation-delay:150ms]" />
                  <span className="h-2 w-2 rounded-full bg-primary animate-bounce [animation-delay:300ms]" />
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="border-t p-3 flex gap-2">
          <Input
            placeholder="Type your question…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            disabled={loading}
          />
          <Button onClick={send} disabled={loading || !input.trim()} size="icon">
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </Card>
    </PageShell>
  );
}
