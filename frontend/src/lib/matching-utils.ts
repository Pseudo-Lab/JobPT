export const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null;

export const toStringValue = (value: unknown): string | undefined => {
  if (typeof value === "string" && value.trim().length > 0) {
    return value;
  }
  return undefined;
};

export const toNumberValue = (value: unknown): number | undefined => {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string") {
    const cleaned = value.replace(/[^\d.]/g, "");
    if (!cleaned) return undefined;
    const parsed = Number.parseFloat(cleaned);
    return Number.isNaN(parsed) ? undefined : parsed;
  }
  return undefined;
};

export const pickFirstString = (
  source: Record<string, unknown> | null | undefined,
  keys: string[],
): string | undefined => {
  if (!source) return undefined;
  for (const key of keys) {
    const candidate = toStringValue(source[key]);
    if (candidate) return candidate;
  }
  return undefined;
};

export const pickFirstNumber = (
  source: Record<string, unknown> | null | undefined,
  keys: string[],
): number | undefined => {
  if (!source) return undefined;
  for (const key of keys) {
    const candidate = toNumberValue(source[key]);
    if (candidate !== undefined) return candidate;
  }
  return undefined;
};

export const toRecordArray = (input: unknown): Record<string, unknown>[] => {
  if (Array.isArray(input)) {
    return input
      .map((item) => (isRecord(item) ? item : null))
      .filter((item): item is Record<string, unknown> => item !== null);
  }
  if (isRecord(input)) {
    return [input];
  }
  return [];
};

export const formatMatchLabel = (value?: number): string | null => {
  if (value === undefined) return null;
  const percent = value <= 1 ? Math.round(value * 100) : Math.round(value);
  if (Number.isNaN(percent)) return null;
  return `${percent}% Match`;
};

export const resolveRemoteLabel = (
  source: Record<string, unknown> | null | undefined,
): string | undefined => {
  if (!source) return undefined;
  const raw =
    source["remote"] ??
    source["is_remote"] ??
    source["remote_available"] ??
    source["remote_preference"];
  if (typeof raw === "boolean") {
    return raw ? "원격 가능" : "현장 근무";
  }
  if (typeof raw === "string") {
    const normalized = raw.toLowerCase();
    if (
      ["true", "yes", "remote", "available", "prefer"].some((token) =>
        normalized.includes(token),
      )
    ) {
      return "원격 가능";
    }
    if (
      ["false", "no", "onsite", "office", "현장", "불가"].some((token) =>
        normalized.includes(token),
      )
    ) {
      return "현장 근무";
    }
    return raw;
  }
  return undefined;
};
