export interface ManualJDFormProps {
  onSubmit: (company: string, jdUrl: string, jdText: string) => void;
  onBack: () => void;
}

export interface ResultViewProps {
  pdfError: string | null;
  isPdf: boolean;
  sectionBoxes: SectionBox[];
  handleSectionClick: (box: SectionBox) => void;
  thumbnailUrl: string | null;
  company: string;
  JD: string;
  JD_url: string;
  output: string;
  handleBackToUpload: () => void;
  pdfUrl: string | null;
  rawElements: RawElement[];
  userResumeDraft: string;
  setUserResumeDraft: (val: string) => void;
  userResume: string;
  setUserResume: (val: string) => void;
}

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