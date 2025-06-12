export interface UploadViewProps {
  file: File | null;
  status: string;
  isDragging: boolean;
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  handleFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  handleAnalyze: () => void;
  handleDrop: (e: React.DragEvent<HTMLDivElement>) => void;
  setIsDragging: (dragging: boolean) => void;
  location: string[];
  remote: boolean[];
  jobType: string[];
  setLocation: (val: string[]) => void;
  setRemote: (val: boolean[]) => void;
  setJobType: (val: string[]) => void;
  handleManualJD: () => void;
} 