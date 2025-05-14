"use client";

import { useState, useRef, useEffect } from "react";
import Head from "next/head";
import DOMPurify from "dompurify";
import { marked } from "marked";
import UploadView from "./components/UploadView";
import ResultView from "./components/ResultView";
import type { RawElement } from "./components/PdfHighlighterView";

// PDF 내 특정 영역(섹션)을 표시하기 위한 타입 정의
type SectionBox = {
    id: string;
    title: string;
    x: number;
    y: number;
    width: number;
    height: number;
    text: string;
};

export default function Home() {
    // 기본 상태 관리
    const [file, setFile] = useState<File | null>(null);
    const [status, setStatus] = useState("Ready");
    const [JD, setJD] = useState("");
    const [output, setOutput] = useState("");
    const [JD_url, setJDUrl] = useState("");
    const [company, setCompany] = useState("");
    const [thumbnailUrl, setThumbnailUrl] = useState<string | null>(null);
    const [isPdf, setIsPdf] = useState(false);
    const [pdfUrl, setPdfUrl] = useState<string | null>(null);
    const [pdfError, setPdfError] = useState<string | null>(null);
    const [sectionBoxes, setSectionBoxes] = useState<SectionBox[]>([]);
    const [rawElements, setRawElements] = useState<RawElement[]>([]);
    const [viewMode, setViewMode] = useState<"upload" | "result">("upload");
    const [resumePath, setResumePath] = useState("");
    const [isDragging, setIsDragging] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const [location, setLocation] = useState("");
    const [remote, setRemote] = useState("any"); // "yes", "no", "any"
    const [jobType, setJobType] = useState("any"); // "full-time", "part-time", "any"

    const handleSectionClick = (box: SectionBox) => {
        console.log("Clicked section:", box.id, box.text);
    };

    // 채팅창 높이 조정
    const adjustChatHeight = () => {
        const chatMessages = document.getElementById("chat-messages");
        if (!chatMessages) return;

        const messageCount = chatMessages.childElementCount;
        let newHeight = "160px";

        if (messageCount > 2) {
            newHeight = "500px";
        }

        const isScrolledToBottom = chatMessages.scrollHeight - chatMessages.clientHeight <= chatMessages.scrollTop + 10;
        const oldScrollHeight = chatMessages.scrollHeight;

        chatMessages.style.height = newHeight;

        if (isScrolledToBottom) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        } else {
            const heightDifference = chatMessages.scrollHeight - oldScrollHeight;
            chatMessages.scrollTop += heightDifference;
        }
    };

    // 채팅 전송 함수
    const getOrCreateSessionId = () => {
        if (typeof window === "undefined") return "";
        let sessionId = window.localStorage.getItem("session_id");
        if (!sessionId) {
            sessionId = typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : String(Date.now());
            window.localStorage.setItem("session_id", sessionId);
        }
        return sessionId;
    };

    const sendMessage = async () => {
        const chatMessages = document.getElementById("chat-messages");
        const chatInput = document.getElementById("chat-input") as HTMLInputElement | null;
        if (!chatMessages || !chatInput) return;

        const message = chatInput.value.trim();
        if (!message) return;

        const userMessageDiv = document.createElement("div");
        userMessageDiv.className = "mb-3 text-right";
        userMessageDiv.innerHTML = `
      <div class="inline-block px-4 py-2 rounded-lg bg-indigo-600 text-white max-w-[90%]">
        <div class="prose prose-sm">${DOMPurify.sanitize(marked.parseInline(message))}</div>
      </div>
    `;
        chatMessages.appendChild(userMessageDiv);
        chatInput.value = "";
        adjustChatHeight();
        chatMessages.scrollTop = chatMessages.scrollHeight;

        const botTypingDiv = document.createElement("div");
        botTypingDiv.className = "mb-3 text-left animate-pulse";
        botTypingDiv.id = "bot-typing";
        botTypingDiv.innerHTML = `
      <div class="inline-block px-4 py-2 rounded-lg bg-gray-200 text-gray-800 max-w-[90%]">
        <div class="prose prose-sm">...답변 생성중...</div>
      </div>
    `;
        chatMessages.appendChild(botTypingDiv);
        adjustChatHeight();
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const session_id = getOrCreateSessionId();
            const requestData = {
                message,
                resume_path: resumePath || "",
                company_name: company || "",
                jd: JD || "",
                session_id,
            };

            const response = await fetch("http://localhost:8000/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(requestData),
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(errorText);
            }

            const data = await response.json();
            chatMessages.removeChild(botTypingDiv);

            const botMessageDiv = document.createElement("div");
            botMessageDiv.className = "mb-3 text-left";
            const sanitizedHtml = DOMPurify.sanitize(marked.parse(data.response));
            botMessageDiv.innerHTML = `
        <div class="inline-block px-4 py-2 rounded-lg bg-gray-200 text-gray-800 max-w-[90%]">
          <div class="prose prose-sm">${sanitizedHtml}</div>
        </div>
      `;
            chatMessages.appendChild(botMessageDiv);
            adjustChatHeight();
            chatMessages.scrollTop = chatMessages.scrollHeight;
        } catch (error) {
            console.error("챗봇 API 호출 오류:", error);
            if (chatMessages.contains(botTypingDiv)) chatMessages.removeChild(botTypingDiv);

            const errorMessageDiv = document.createElement("div");
            errorMessageDiv.className = "mb-3 text-left";
            const errorHtml = DOMPurify.sanitize(marked.parseInline("죄송합니다. 오류가 발생했습니다. 잠시 후 다시 시도해주세요."));
            errorMessageDiv.innerHTML = `
        <div class="inline-block px-4 py-2 rounded-lg bg-red-100 text-red-800 max-w-[90%]">
          <div class="prose prose-sm">${errorHtml}</div>
        </div>
      `;
            chatMessages.appendChild(errorMessageDiv);
            adjustChatHeight();
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    };

    useEffect(() => {
        if (viewMode !== "result") return;

        const sendButton = document.getElementById("send-message");
        const chatInput = document.getElementById("chat-input");

        if (!sendButton || !chatInput) return;

        sendButton.addEventListener("click", sendMessage);
        chatInput.addEventListener("keypress", function handleKeyPress(e) {
            if (e.key === "Enter") {
                sendMessage();
            }
        });

        adjustChatHeight();

        return () => {
            sendButton.removeEventListener("click", sendMessage);
            chatInput.removeEventListener("keypress", function handleKeyPress(e) {
                if (e.key === "Enter") {
                    sendMessage();
                }
            });
        };
    }, [viewMode, resumePath, company, JD]);

    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = e.target.files?.[0];
        if (selectedFile) {
            setFile(selectedFile);
            const isPdfFile = selectedFile.type === "application/pdf";
            setIsPdf(isPdfFile);
            if (isPdfFile) {
                setPdfUrl(URL.createObjectURL(selectedFile));
                setThumbnailUrl(null);
            } else {
                setThumbnailUrl(URL.createObjectURL(selectedFile));
            }
        }
    };

    const handleDrop = async (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        setIsDragging(false);

        const droppedFiles = e.dataTransfer.files;
        if (droppedFiles && droppedFiles.length > 0) {
            const droppedFile = droppedFiles[0];
            setFile(droppedFile);
            const isPdfFile = droppedFile.type === "application/pdf";
            setIsPdf(isPdfFile);
            if (isPdfFile) {
                setPdfUrl(URL.createObjectURL(droppedFile));
                setThumbnailUrl(null);
            } else {
                setThumbnailUrl(URL.createObjectURL(droppedFile));
            }
        }
    };

    const handleAnalyze = async () => {
        if (!file) return;

        setStatus("Processing...");

        const formData = new FormData();
        formData.append("file", file);
        formData.append("location", location);
        formData.append("remote", remote);
        formData.append("job_type", jobType);

        try {
            const uploadRes = await fetch("http://localhost:8000/upload", {
                method: "POST",
                body: formData,
            });
            const { resume_path } = await uploadRes.json();
            setResumePath(resume_path);

            const res = await fetch("http://localhost:8000/matching", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ resume_path }),
            });
            const data = await res.json();
            setJD(data.JD);
            setOutput(data.output);
            setJDUrl(data.JD_url);
            setCompany(data.name);
            setStatus("Complete!");

            // Upstage parsing
            try {
                const upstageForm = new FormData();
                upstageForm.append("file", file);
                const upstageRes = await fetch("/api/upstage-parse", {
                    method: "POST",
                    body: upstageForm,
                });
                const upstageData = await upstageRes.json();
                console.log("[Upstage API Response]", upstageData);

                const boxes = (upstageData.elements || []).map((e: any) => ({
                    id: String(e.id),
                    title: e.category,
                    x: 0,
                    y: 0,
                    width: 0,
                    height: 0,
                    text: e.content.markdown || e.content.text || "",
                }));
                setSectionBoxes(boxes);
                setRawElements(
                    (upstageData.elements || []).map((e: any) => ({
                        id: e.id,
                        page: e.page,
                        coordinates: e.coordinates,
                        content: { text: e.content.text, markdown: e.content.markdown },
                    }))
                );
            } catch (e) {
                console.error("[Upstage API Error]", e);
                setSectionBoxes([]);
            }

            setViewMode("result");
        } catch (error) {
            console.error("분석 중 오류 발생:", error);
            setStatus("Error: 서버 연결 실패");
        }
    };

    const handleBackToUpload = () => {
        setViewMode("upload");
    };

    const renderUploadView = () => (
        <UploadView
            file={file}
            status={status}
            isDragging={isDragging}
            fileInputRef={fileInputRef}
            handleFileChange={handleFileChange}
            handleAnalyze={handleAnalyze}
            handleDrop={handleDrop}
            setIsDragging={setIsDragging}
            location={location}
            remote={remote}
            jobType={jobType}
            setLocation={setLocation}
            setRemote={setRemote}
            setJobType={setJobType}
        />
    );

    return (
        <>
            <Head>
                <title>JobPT | Resume Analyzer</title>
                <meta name="description" content="Resume analyzer for job descriptions" />
                <link rel="icon" href="/favicon.ico" />
            </Head>

            <main className="bg-gray-50 min-h-screen">
                {viewMode === "upload" ? (
                    renderUploadView()
                ) : (
                    <ResultView
                        pdfError={pdfError}
                        isPdf={isPdf}
                        sectionBoxes={sectionBoxes}
                        handleSectionClick={handleSectionClick}
                        thumbnailUrl={thumbnailUrl}
                        company={company}
                        JD={JD}
                        JD_url={JD_url}
                        output={output}
                        handleBackToUpload={handleBackToUpload}
                        pdfUrl={pdfUrl}
                        rawElements={rawElements}
                    />
                )}
            </main>
        </>
    );
}
