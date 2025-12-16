"use client";

import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { Document, Page, pdfjs } from "react-pdf";
import { pdfWorkerSrc } from "@/lib/pdfWorkerLoader";

import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

pdfjs.GlobalWorkerOptions.workerSrc = pdfWorkerSrc;

interface PdfHighlighterViewProps {
  pdfUrl: string;
  className?: string;
  emptyPlaceholder?: React.ReactNode;
  onAskSelection?: (selection: string) => void;
}

const PdfHighlighterView: React.FC<PdfHighlighterViewProps> = ({
  pdfUrl,
  className,
  emptyPlaceholder,
  onAskSelection,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState<number>(0);
  const [numPages, setNumPages] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [popover, setPopover] = useState({
    isVisible: false,
    top: 0,
    left: 0,
    text: "",
  });

  useEffect(() => {
    const element = containerRef.current;
    if (!element) return undefined;

    const observer = new ResizeObserver((entries) => {
      entries.forEach((entry) => {
        setContainerWidth(entry.contentRect.width);
      });
    });
    observer.observe(element);

    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    setNumPages(0);
    setError(null);
    setIsLoading(true);
  }, [pdfUrl]);

  const widthForPage = useMemo(() => {
    const padding = 32;
    const fallback = 1280;
    if (!containerWidth) return fallback;
    const available = containerWidth - padding;
    return Math.min(Math.max(available, 700), 1100);
  }, [containerWidth]);

  const hidePopover = useCallback(() => {
    setPopover((prev) => ({ ...prev, isVisible: false, text: "" }));
  }, []);

  const handleSelectionChange = useCallback(() => {
    const selection = window.getSelection();
    const container = containerRef.current;

    if (!selection || selection.isCollapsed || !container) {
      hidePopover();
      return;
    }

    const selectedText = selection.toString().trim();
    if (!selectedText) {
      hidePopover();
      return;
    }

    if (selection.rangeCount === 0) {
      hidePopover();
      return;
    }

    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    const containerRect = container.getBoundingClientRect();

    if (
      rect.width === 0 ||
      rect.height === 0 ||
      rect.bottom < containerRect.top ||
      rect.top > containerRect.bottom
    ) {
      hidePopover();
      return;
    }

    const top = rect.top - containerRect.top + container.scrollTop - 48;
    const left = rect.left - containerRect.left + container.scrollLeft + rect.width / 2;

    setPopover({
      isVisible: true,
      top,
      left,
      text: selectedText,
    });
  }, [hidePopover]);

  useEffect(() => {
    document.addEventListener("selectionchange", handleSelectionChange);
    document.addEventListener("mouseup", handleSelectionChange);

    return () => {
      document.removeEventListener("selectionchange", handleSelectionChange);
      document.removeEventListener("mouseup", handleSelectionChange);
    };
  }, [handleSelectionChange]);

  if (!pdfUrl) {
    return (
      <div
        className={[
          "flex h-full min-h-[360px] items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50 text-sm text-slate-400",
          className,
        ]
          .filter(Boolean)
          .join(" ")}
      >
        {emptyPlaceholder || "이력서 파일이 아직 준비되지 않았습니다."}
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={[
        "relative flex h-full max-h-[90vh] flex-col overflow-auto rounded-2xl border border-slate-200 bg-white shadow-inner",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <Document
        file={pdfUrl}
        onLoadSuccess={({ numPages: totalPages }) => {
          setNumPages(totalPages);
          setIsLoading(false);
        }}
        onLoadError={(err) => {
          console.error("[PDF] Failed to load", err);
          setError("PDF를 불러오지 못했습니다.");
          setIsLoading(false);
        }}
        loading={
          <div className="flex flex-1 items-center justify-center text-sm text-slate-400">
            PDF를 불러오는 중입니다...
          </div>
        }
        error={
          <div className="flex flex-1 items-center justify-center text-sm text-rose-500">
            PDF를 불러오지 못했습니다.
          </div>
        }
        className="flex flex-col items-center gap-6 p-4"
      >
        {error ? (
          <div className="flex flex-1 items-center justify-center text-sm text-rose-500">
            {error}
          </div>
        ) : (
          Array.from(new Array(numPages), (_el, index) => (
            <Page
              key={`page_${index + 1}`}
              pageNumber={index + 1}
              width={widthForPage ?? 680}
              scale={0.9}
              renderAnnotationLayer
              renderTextLayer
            />
          ))
        )}
      </Document>

      {isLoading && !error && (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center bg-white/60 text-sm text-slate-400">
          로딩 중...
        </div>
      )}

      {popover.isVisible && (
        <div
          className="absolute z-30 -translate-x-1/2 rounded-xl bg-white px-3 py-2 text-xs shadow-lg ring-1 ring-slate-200"
          style={{ top: popover.top, left: popover.left }}
        >
          <div className="max-w-xs whitespace-pre-wrap text-center text-[11px] leading-snug text-slate-600">
            {popover.text}
          </div>
          <div className="mt-2 flex justify-center">
            <button
              type="button"
              className="flex items-center gap-1 rounded-full bg-blue-500 px-3 py-1 text-[11px] font-semibold text-white transition hover:bg-blue-600"
              onClick={() => {
                if (onAskSelection) {
                  onAskSelection(popover.text);
                }
                hidePopover();
                window.getSelection()?.removeAllRanges();
              }}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
                className="h-3.5 w-3.5"
              >
                <path d="M9 2a7 7 0 100 14h2a7 7 0 000-14H9zM8.5 7.5a.5.5 0 010-1h.25a1.75 1.75 0 013.36-.76.5.5 0 10.88-.48A2.75 2.75 0 008.75 5.5H8.5a1.5 1.5 0 000 3h1a.5.5 0 010 1H9a.5.5 0 000 1h.5a1.5 1.5 0 100-3H9 8.5zm.75 5.75a.75.75 0 111.5 0 .75.75 0 01-1.5 0z" />
              </svg>
              Ask AI
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default PdfHighlighterView;
