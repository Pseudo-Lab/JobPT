// src/app/editor/page.tsx
"use client";

import { useEffect, useRef, useState } from "react";
import {
  ensureMockSessionData,
  isMockEnabled,
} from "@/lib/mockData";
import ResumeSummaryView, { ResumeSummaryData } from "@/components/evaluate/ResumeSummaryView";
import AppHeader from "@/components/common/AppHeader";

type ChatRole = "assistant" | "user";

interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  createdAt: number;
  title?: string;
  variant?: "summary";
}

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

const EditorPage = () => {
  const [resumePath, setResumePath] = useState<string | null>(null);
  const [userResume, setUserResume] = useState<string>("");
  const [draftMessage, setDraftMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [isComposing, setIsComposing] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);

  const defaultResumeSummary: ResumeSummaryData = {
    name: "김길동",
    phone: "010-0000-0000",
    email: "email@gmail.com",
    summary:
      "안녕하세요, 서비스 기획자 김길동입니다. 간단한 자기소개가 이곳에 들어갑니다. 간단한 자기소개가 이곳에 들어갑니다. 간단한 자기소개가 이곳에 들어갑니다.",
    experiences: [
      {
        company: "회사명",
        period: "0000.00 ~ 재직중 (0년 00개월)",
        title: "담당한 역할 타이틀",
        description:
          "담당한 역할과 업무 등에 대한 내용이 이곳에 들어갑니다. 담당한 역할과 업무 등에 대한 내용이 이곳에 들어갑니다. 담당한 역할과 업무 등에 대한 내용이 이곳에 들어갑니다.",
        logoUrl: "/logo/main_logo.png",
      },
      {
        company: "회사명",
        period: "0000.00 ~ 0000.00",
        title: "담당한 역할 타이틀",
        description:
          "담당한 역할과 업무 등에 대한 내용이 이곳에 들어갑니다. 담당한 역할과 업무 등에 대한 내용이 이곳에 들어갑니다. 담당한 역할과 업무 등에 대한 내용이 이곳에 들어갑니다.",
      },
    ],
    skills: ["Python", "Figma", "React", "TypeScript", "Next.js", "Git"],
    certifications: [
      { name: "자격증 이름", date: "0000.00", note: "취득" },
      { name: "수상내역", date: "0000.00", note: "수상" },
    ],
    languages: [
      {
        name: "영어",
        details: ["OPIc IM1 (Intermediate Mid)", "TOEIC 990"],
      },
      {
        name: "중국어",
        details: ["HSK 6급"],
      },
    ],
    links: [{ label: "https://github.com/gildong", url: "https://github.com/gildong" }],
  };

  useEffect(() => {
    if (isMockEnabled) {
      ensureMockSessionData();
    }
    if (typeof window === "undefined") return;

    const session = window.sessionStorage;
    const sessionResume = session.getItem("resume_path");
    setResumePath(sessionResume);

    const storedResume =
      window.localStorage.getItem("user_resume") ??
      sessionStorage.getItem("user_resume") ??
      "";
    setUserResume(storedResume);
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
    const trimmed = rawMessage.trim();
    if (!trimmed) return;
    if (!resumePath) {
      alert("이력서가 없습니다. 업로드 단계를 먼저 완료해주세요.");
      return;
    }

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: trimmed,
      createdAt: Date.now(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setDraftMessage("");

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
          message: trimmed,
          resume_path: resumePath,
          company: "",
          jd: "",
          session_id: sessionId,
          user_resume: userResume,
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

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("[Chat] Failed to send message", error);
      setMessages((prev) => [
        ...prev,
        {
          id: `assistant-error-${Date.now()}`,
          role: "assistant",
          content: "죄송합니다. 지금은 답변을 생성할 수 없습니다. 잠시 후 다시 시도해주세요.",
          createdAt: Date.now(),
        },
      ]);
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
            <ResumeSummaryView summary={defaultResumeSummary} />

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
                  <div className="space-y-5">
                    {messages.map((message) => {
                      const isUser = message.role === "user";
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
                            <p className="whitespace-pre-wrap">{message.content}</p>
                            <span className={`block text-[11px] ${isUser ? "text-blue-100" : "text-slate-400"}`}>
                              {formatTime(message.createdAt)}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

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
