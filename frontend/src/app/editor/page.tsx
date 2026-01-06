// src/app/editor/page.tsx
"use client";

import { useEffect, useRef, useState } from "react";
import ResumeSummaryView, { ResumeSummaryData } from "@/components/evaluate/ResumeSummaryView";
import AppHeader from "@/components/common/AppHeader";
import { isRecord, pickFirstString } from "@/lib/matching-utils";
import DOMPurify from "dompurify";
import { marked } from "marked";

type ChatRole = "assistant" | "user";

interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  createdAt: number;
  title?: string;
  variant?: "summary";
}

interface JobContext {
  title?: string | undefined;
  company?: string | undefined;
  jd?: string | undefined;
  jobUrl?: string | undefined;
  matchLabel?: string | null | undefined;
}

const parseStoredJobContext = (raw: string | null): JobContext | null => {
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    if (!isRecord(parsed)) return null;

    const rawJob = isRecord(parsed.raw) ? parsed.raw : undefined;
    const fallbackJd = pickFirstString(rawJob, ["JD"]);

    return {
      title:
        typeof parsed.title === "string"
          ? parsed.title
          : pickFirstString(rawJob, ["job_title", "title"]),
      company:
        typeof parsed.company === "string"
          ? parsed.company
          : pickFirstString(rawJob, ["company", "name", "organization"]),
      jd:
        typeof parsed.jd === "string" && parsed.jd.trim().length > 0
          ? parsed.jd
          : fallbackJd,
      jobUrl:
        typeof parsed.jobUrl === "string"
          ? parsed.jobUrl
          : pickFirstString(rawJob, ["job_url", "url", "link"]),
      matchLabel:
        typeof parsed.matchLabel === "string"
          ? parsed.matchLabel
          : pickFirstString(rawJob, ["match", "score_label", "match_label"]),
    };
  } catch (error) {
    console.warn("[Editor] Failed to parse stored job context", error);
    return null;
  }
};

const formatTime = (timestamp: number) => {
  const date = new Date(timestamp);
  return `${date.getHours().toString().padStart(2, "0")}:${date
    .getMinutes()
    .toString()
    .padStart(2, "0")}`;
};

const ChatAvatar = ({
  role,
  variant,
  size = 40,
}: {
  role: ChatRole;
  variant?: "summary";
  size?: number;
}) => {
  const isUser = role === "user";
  let bgClass = isUser ? "bg-[rgb(96,150,222)] text-white" : "bg-[rgb(96,150,222)] text-white";
  let icon = isUser ? (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-5 w-5">
      <circle cx="12" cy="8.5" r="3" />
      <path d="M5.5 19a5.5 5.5 0 015.5-5.5h2a5.5 5.5 0 015.5 5.5v.5a1.5 1.5 0 01-1.5 1.5H7a1.5 1.5 0 01-1.5-1.5V19z" />
    </svg>
  ) : (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} className="h-5 w-5">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.75l-1.219 2.471L8.25 10.5l2.531 1.279L12 14.25l1.219-2.471L15.75 10.5l-2.531-1.279L12 6.75z" />
    </svg>
  );

  if (!isUser && variant === "summary") {
    bgClass = "bg-[rgb(96,150,222)] text-white";
    icon = (
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} className="h-5 w-5">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.75l-1.219 2.471L8.25 10.5l2.531 1.279L12 14.25l1.219-2.471L15.75 10.5l-2.531-1.279L12 6.75z" />
      </svg>
    );
  }

  return (
    <div
      className={`flex items-center justify-center rounded-full ${bgClass}`}
      style={{ width: size, height: size }}
    >
      {icon}
    </div>
  );
};

const defaultResumeSummary: ResumeSummaryData = {
  name: "",
  phone: "",
  email: "",
  summary: "",
  experiences: [],
  skills: [],
  certifications: [],
  languages: [],
  links: [],
};

const EditorPage = () => {
  const [resumePath, setResumePath] = useState<string | null>(null);
  const [draftMessage, setDraftMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [isComposing, setIsComposing] = useState(false);
  const [attachments, setAttachments] = useState<
    { id: string; label: string; content: string }[]
  >([]);
  const [jobContext, setJobContext] = useState<JobContext | null>(null);
  const [resumeSummary, setResumeSummary] = useState<ResumeSummaryData>(() => {
    if (typeof window !== "undefined") {
      const raw = window.sessionStorage.getItem("resume_summary");
      if (raw) {
        try {
          const parsed = JSON.parse(raw);
          if (parsed && typeof parsed === "object") {
            return { ...defaultResumeSummary, ...(parsed as ResumeSummaryData) };
          }
        } catch (error) {
          console.warn("[Editor] Failed to parse stored resume summary on init", error);
        }
      }
    }
    return defaultResumeSummary;
  });
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const session = window.sessionStorage;
    const sessionResume = session.getItem("resume_path");
    setResumePath(sessionResume);

    // Ensure latest resume summary is in session for immediate use
    const rawSummary = session.getItem("resume_summary");
    if (rawSummary) {
      try {
        const parsed = JSON.parse(rawSummary);
        if (parsed && typeof parsed === "object") {
          setResumeSummary({ ...defaultResumeSummary, ...(parsed as ResumeSummaryData) });
        }
      } catch (error) {
        console.warn("[Editor] Failed to parse stored resume summary", error);
      }
    }

    const storedJobContext = parseStoredJobContext(session.getItem("selected_job_context"));
    if (storedJobContext) {
      setJobContext(storedJobContext);
    } else {
      const fallbackJd = session.getItem("jd_text");
      if (fallbackJd) {
        setJobContext({ jd: fallbackJd });
      }
    }
  }, []);

  useEffect(() => {
    if (messages.length > 0) return;
    setMessages([
      {
        id: "assistant-welcome",
        role: "assistant",
        content:
          "안녕하세요. 이력서 내용을 기반으로 수정이나 보완이 필요하신 부분을 말씀해주세요. 함께 다듬어볼게요!",
        createdAt: Date.now(),
      },
    ]);
  }, [messages.length]);

  useEffect(() => {
    const container = listRef.current;
    if (!container) return;
    container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });
  }, [messages]);


  const handleSendMessage = async (presetMessage?: string) => {
    if (isSending) return;
    if (isComposing) return;
    const rawMessage = presetMessage ?? draftMessage;
    const trimmedMessage = rawMessage.trim();
    if (!trimmedMessage && attachments.length === 0) return;
    if (!resumePath) {
      alert("이력서가 없습니다. 업로드 단계를 먼저 완료해주세요.");
      return;
    }

    console.log("[Chat] user message", trimmedMessage);

    const companyForApi = jobContext?.company ?? "";
    const jdForApi = jobContext?.jd ?? "";
    const jobTitleForApi = jobContext?.title ?? "";
    const jobUrlForApi = jobContext?.jobUrl ?? "";

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: trimmedMessage,
      createdAt: Date.now(),
    };
    const typingMessage: ChatMessage = {
      id: "assistant-typing",
      role: "assistant",
      content: "답변 생성중...",
      createdAt: Date.now() + 0.5,
    };
    const historyForApi = [...messages, userMessage]
      .filter((msg) => msg.role === "assistant" || msg.role === "user")
      .slice(-10)
      .map((msg) => ({ role: msg.role, content: msg.content }));

    setMessages((prev) => [...prev, userMessage, typingMessage]);
    setDraftMessage("");
    // 첨부 표시를 즉시 비워 UI 칩을 빠르게 숨기고, 이미 조합한 메시지에는 포함된 상태를 유지합니다.
    setAttachments([]);

    const sessionId =
      typeof window !== "undefined"
        ? window.localStorage.getItem("session_id") ||
          (() => {
            const generated =
              typeof crypto !== "undefined" && crypto.randomUUID
                ? crypto.randomUUID()
                : String(Date.now());
            window.localStorage.setItem("session_id", generated);
            return generated;
          })()
        : "";

    setIsSending(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: trimmedMessage,
          resume_path: resumePath,
          company: companyForApi,
          jd: jdForApi,
          session_id: sessionId,
          job_title: jobTitleForApi,
          job_url: jobUrlForApi,
          conversation_history: historyForApi,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText);
      }

      const data = await response.json();
      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now() + 1}`,
        role: "assistant",
        content: data.response ?? "응답을 불러오지 못했습니다.",
        createdAt: Date.now() + 1,
      };

      setMessages((prev) =>
        [...prev].filter((m) => m.id !== "assistant-typing").concat(assistantMessage),
      );
    } catch (error) {
      console.error("[Chat] Failed to send message", error);
      setMessages((prev) => {
        const withoutTyping = [...prev].filter((m) => m.id !== "assistant-typing");
        return [
          ...withoutTyping,
          {
            id: `assistant-error-${Date.now()}`,
            role: "assistant",
            content: "죄송합니다. 지금은 답변을 생성할 수 없습니다. 잠시 후 다시 시도해주세요.",
            createdAt: Date.now(),
          },
        ];
      });
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#1f1f1f]">
      <AppHeader />

      <main className="min-h-[calc(100vh-4rem)] bg-[#f6f7fb]">
        <div className="mx-auto max-w-[90rem] px-4 py-12 sm:px-8">
          <div className="grid gap-6 lg:grid-cols-[minmax(0,4fr)_minmax(0,3fr)]">
            <ResumeSummaryView
              summary={resumeSummary}
              editable
              // onAttach={(item) => {
              //   setAttachments((prev) => {
              //     const exists = prev.find((p) => p.id === item.id);
              //     if (exists) {
              //       return prev.map((p) => (p.id === item.id ? item : p));
              //     }
              //     return [...prev, item];
              //   });
              // }}
              onChange={(next) => {
                setResumeSummary(next);
                if (typeof window !== "undefined") {
                  window.sessionStorage.setItem("resume_summary", JSON.stringify(next));
                  const currentResume =
                    resumePath ?? window.sessionStorage.getItem("resume_path");
                  if (currentResume) {
                    window.sessionStorage.setItem("resume_summary_path", currentResume);
                  }
                }
              }}
            />

            <div className="flex h-full flex-col gap-6">
              <section className="flex h-full min-h-[70vh] flex-col rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
                <header className="flex items-center justify-between">
                  <div>
                    <h2 className="text-2xl font-semibold text-slate-900">AI Assistant</h2>
                  </div>
                </header>
                <div
                  ref={listRef}
                  className="mt-6 mb-6 flex-1 min-h-[320px] max-h-[1100px] overflow-y-auto pr-1"
                >
                  <div className="space-y-6 pb-1">
                    {messages.map((message) => {
                      const isUser = message.role === "user";
                      const parsed = marked.parse(message.content ?? "");
                      const assistantHtml =
                        typeof parsed === "string" ? DOMPurify.sanitize(parsed) : "";
                      return (
                        <div key={message.id} className={`flex items-start gap-3 ${isUser ? "flex-row-reverse text-right" : ""}`}>
                          <ChatAvatar role={message.role} />
                          <div
                            className={`w-full max-w-[85%] rounded-3xl px-4 py-3 text-sm leading-relaxed shadow-sm ${
                              isUser
                                ? "bg-[rgb(96,150,222)] text-white"
                                : "bg-slate-50 text-slate-700"
                            }`}
                          >
                            {message.title && (
                              <p
                                className={`text-sm font-semibold ${
                                  isUser ? "text-white" : "text-slate-900"
                                }`}
                              >
                                {message.title}
                              </p>
                            )}
                            {isUser ? (
                              <p className="whitespace-pre-wrap">{message.content}</p>
                            ) : (
                              <div
                                className="prose prose-sm max-w-none text-slate-700"
                                dangerouslySetInnerHTML={{ __html: assistantHtml }}
                              />
                            )}
                            <span className={`block text-[11px] ${isUser ? "text-blue-100" : "text-slate-400"}`}>
                              {formatTime(message.createdAt)}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {attachments.length > 0 && (
                  <div className="mb-3 flex flex-wrap gap-2">
                    {attachments.map((item) => {
                      const snippet =
                        item.content.length > 40
                          ? `${item.content.slice(0, 40)}…`
                          : item.content;
                      return (
                        <span
                          key={item.id}
                          className="relative inline-flex items-center gap-2 rounded-full bg-[#2f2f2f] px-4 py-1 text-xs font-semibold text-white shadow-sm"
                        >
                          <span className="pl-4 pr-1 max-w-[200px] truncate">
                            {item.label} · {snippet}
                          </span>
                          <button
                            type="button"
                            onClick={() =>
                              setAttachments((prev) =>
                                prev.filter((attachment) => attachment.id !== item.id),
                              )
                            }
                            className="text-white/70 transition hover:text-white"
                            aria-label={`${item.label} 첨부 제거`}
                          >
                            ×
                          </button>
                        </span>
                      );
                    })}
                  </div>
                )}

                <div className="mt-auto rounded-3xl border border-slate-200 bg-white px-4 py-3 shadow-inner">
                  <div className="flex items-center gap-3">
                    <input
                      type="text"
                      value={draftMessage}
                      onChange={(event) => setDraftMessage(event.target.value)}
                      placeholder="입력하세요."
                      className="flex-1 border-0 bg-transparent text-sm focus:outline-none"
                      onCompositionStart={() => setIsComposing(true)}
                      onCompositionEnd={() => setIsComposing(false)}
                      onKeyDown={(event) => {
                        if (event.nativeEvent.isComposing || isComposing) return;
                        if (event.key === "Enter" && !event.shiftKey) {
                          event.preventDefault();
                          handleSendMessage();
                        }
                      }}
                    />
                    <button
                      type="button"
                      onClick={() => handleSendMessage()}
                      disabled={isSending}
                      className="flex h-10 w-10 items-center justify-center rounded-full bg-[rgb(96,150,222)] text-white transition hover:bg-[rgb(86,140,212)]"
                      aria-label="메시지 전송"
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        strokeWidth={1.5}
                        stroke="currentColor"
                        className="h-5 w-5"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 5.25l13.5 6.75-13.5 6.75L9 12 5.25 5.25z" />
                      </svg>
                    </button>
                  </div>
                </div>
              </section>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default EditorPage;
