"use client";
import "react-pdf-highlighter/dist/style.css";
import "pdfjs-dist/web/pdf_viewer.css";
import React, { useState, useRef } from "react";
import dynamic from "next/dynamic";


// Dynamic import
const PdfLoader = dynamic(
  () => import("react-pdf-highlighter").then((mod) => mod.PdfLoader),
  { ssr: false }
);
const PdfHighlighter = dynamic(
  () => import("react-pdf-highlighter").then((mod) => mod.PdfHighlighter),
  { ssr: false }
);
const Highlight = dynamic(
  () => import("react-pdf-highlighter").then((mod) => mod.Highlight),
  { ssr: false }
);

export type RawElement = {
  id: number;
  page: number;
  coordinates: { x: number; y: number }[];
  content: { text?: string; markdown?: string };
};

type PdfHighlighterViewProps = {
  pdfUrl: string;
};

const PdfHighlighterView: React.FC<{ pdfUrl: string }> = ({ pdfUrl }) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  return (
    <div ref={scrollRef} className="overflow-auto max-h-[80vh] rounded shadow-inner">
      <PdfLoader url={pdfUrl} beforeLoad={<p>Loading PDF...</p>}>
        {(pdfDocument) => (
          <PdfHighlighter
            pdfDocument={pdfDocument}
            highlights={[]}
            scrollRef={scrollRef}
            enableAreaSelection={() => false}
            onScrollChange={() => {}}
            highlightTransform={() => null}
          />
        )}
      </PdfLoader>
    </div>
  );
};

export default PdfHighlighterView;