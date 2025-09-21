// PDF 관련 타입
export type SectionBox = {
  id: string;
  title: string;
  x: number;
  y: number;
  width: number;
  height: number;
  text: string;
};

export type RawElement = {
  id: string;
  page: number;
  coordinates: any;
  content: { text: string; markdown: string };
};

// PDF Highlighter 관련 타입
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

export interface HighlightProps {
  isScrolledTo: boolean;
  position: IHighlight['position'];
  comment: IHighlight['comment'];
  onClick?: () => void;
} 