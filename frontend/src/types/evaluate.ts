export interface ManualJDFormProps {
  onSubmit: (company: string, jdUrl: string, jdText: string) => void;
  onBack: () => void;
}

export interface ResultViewProps {
  pdfError: string | null;
  isPdf: boolean;
  thumbnailUrl: string | null;
  company: string;
  JD: string;
  JD_url: string;
  output: string;
  handleBackToUpload: () => void;
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
  coordinates: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  content: { text: string; markdown: string };
};

export interface StructuredResume {
  basic_info?: {
    name?: string | null;
    phone?: string | null;
    email?: string | null;
    address?: string | null;
  } | null;
  summary?: string | null;
  careers?: Array<{
    company_name?: string | null;
    period?: string | null;
    employment_type?: string | null;
    role?: string | null;
    achievements?: Array<string | Record<string, unknown>> | null;
  }> | null;
  educations?: Array<{
    school_name?: string | null;
    period?: string | null;
    graduation_status?: string | null;
    major_and_degree?: string | null;
    content?: string | null;
  }> | null;
  skills?: string[] | null;
  activities?: Array<{
    activity_name?: string | null;
    period?: string | null;
    activity_type?: string | null;
    content?: string | null;
  }> | null;
  languages?: Array<{
    language_name?: string | null;
    level?: string | null;
    certification?: string | null;
    acquisition_date?: string | null;
  }> | null;
  links?: string[] | null;
  additional_info?: {
    certifications?: Array<{
      name?: string | null;
      date?: string | null;
      note?: string | null;
    }> | null;
    other_experience?: Array<{
      company_name?: string | null;
      period?: string | null;
      role?: string | null;
    }> | null;
    [key: string]: unknown;
  } | null;
  [key: string]: unknown;
}
