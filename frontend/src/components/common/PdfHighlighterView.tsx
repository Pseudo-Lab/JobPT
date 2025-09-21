"use client";
import React, { useRef } from "react";


export type RawElement = {
  id: number;
  page: number;
  coordinates: { x: number; y: number }[];
  content: { text?: string; markdown?: string };
};


const PdfHighlighterView: React.FC<{ pdfUrl: string }> = ({ pdfUrl }) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  // viewer.html?file=... 경로로 전달 (pdfUrl은 퍼블릭 기준 상대경로 or 절대경로)
  // 예시: /pdfjs/web/viewer.html?file=/uploads/mycv.pdf
  const viewerUrl = `/pdfjs/web/viewer.html?file=${encodeURIComponent(pdfUrl)}`;

  return (
    <div ref={scrollRef} className="overflow-auto max-h-[80vh] rounded shadow-inner">
      <iframe
        src={viewerUrl}
        style={{ width: "100%", height: "80vh", border: "none" }}
        title="PDF Viewer"
        allowFullScreen
      />
    </div>
  );
};

export default PdfHighlighterView;