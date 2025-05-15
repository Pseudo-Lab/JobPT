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
