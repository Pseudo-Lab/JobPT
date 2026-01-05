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

export type BoundingBox = {
  x: number;
  y: number;
  width: number;
  height: number;
};

export type RawElement = {
  id: string;
  page: number;
  coordinates: BoundingBox;
  content: { text?: string | null; markdown?: string | null };
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
  children: (pdfDocument: unknown) => React.ReactNode;
}

export interface PdfHighlighterProps {
  pdfDocument: unknown;
  highlights: IHighlight[];
  enableAreaSelection: (event: unknown) => boolean;
  onScrollChange: () => void;
  onSelectionFinished?: (
    highlight: IHighlight,
    content: unknown,
    hideTip: () => void,
    transform: unknown
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
