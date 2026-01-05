export interface UploadViewProps {
  file: File | null;
  status: string;
  isDragging: boolean;
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  handleFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  handleAnalyze: () => void;
  handleDrop: (e: React.DragEvent<HTMLDivElement>) => void;
  setIsDragging: (dragging: boolean) => void;
  jobPostingUrl: string;
  onJobPostingUrlChange: (url: string) => void;
  handleManualJD?: () => void;
}
