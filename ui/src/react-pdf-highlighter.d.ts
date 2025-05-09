declare module 'react-pdf-highlighter' {
  import React from 'react';

  export interface IHighlight {
    position: {
      boundingRect: { x1: number; y1: number; x2: number; y2: number };
      rects: Array<{ x1: number; y1: number; x2: number; y2: number }>;
      pageNumber: number;
    };
    comment: { text?: string };
  }

  export interface PdfLoaderProps {
    url: string;
    beforeLoad: React.ReactNode;
    children: (pdfDocument: any) => React.ReactNode;
  }
  export class PdfLoader extends React.Component<PdfLoaderProps> {}

  export interface PdfHighlighterProps {
    pdfDocument: any;
    highlights: IHighlight[];
    enableAreaSelection: (event: any) => boolean;
    onScrollChange: () => void;
    onSelectionFinished?: (
      highlight: IHighlight,
      content: any,
      hideTip: () => void,
      transform: any
    ) => void;
    scrollRef?: React.RefObject<HTMLElement>;
    highlightTransform: (highlight: IHighlight, index: number) => React.ReactNode;
  }
  export class PdfHighlighter extends React.Component<PdfHighlighterProps> {}

  export interface HighlightProps {
    isScrolledTo: boolean;
    position: IHighlight['position'];
    comment: IHighlight['comment'];
    onClick?: () => void;
  }
  export class Highlight extends React.Component<HighlightProps> {}

  export class AreaHighlight extends React.Component<any> {}

  const ReactPdfHighlighter: {
    PdfLoader: typeof PdfLoader;
    PdfHighlighter: typeof PdfHighlighter;
    Highlight: typeof Highlight;
    AreaHighlight: typeof AreaHighlight;
  };
  export default ReactPdfHighlighter;
}
