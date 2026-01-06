// src/app/evaluate/page.tsx
"use client";

import Image from "next/image";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import DOMPurify from "dompurify";
import { marked } from "marked";
import {
  formatMatchLabel,
  isRecord,
  pickFirstNumber,
  pickFirstString,
  resolveRemoteLabel,
  toRecordArray,
  toStringValue,
} from "@/lib/matching-utils";
import ResumeSummaryView, {
  ResumeCertification,
  ResumeExperience,
  ResumeLanguage,
  ResumeSummaryData,
} from "@/components/evaluate/ResumeSummaryView";
import AppHeader from "@/components/common/AppHeader";

type ViewState = "loading" | "result" | "error";

const parseStoredMatchingData = (
  raw: string | null,
): Record<string, unknown> | null => {
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    return isRecord(parsed) ? parsed : null;
  } catch (error) {
    console.warn("[Evaluate] Failed to parse stored matching result", error);
    return null;
  }
};

const defaultResumeSummary: ResumeSummaryData = {
  name: "",
  phone: "",
  email: "",
  summary: "",
  experiences: [],
  skills: [],
  certifications: [],
  languages: [],
  links: [],
};

const toStringArray = (value: unknown): string[] =>
  Array.isArray(value)
    ? value
        .map((item) => (typeof item === "string" ? item.trim() : ""))
        .filter(Boolean)
    : [];

const parseAchievements = (value: unknown): string[] => {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => {
      if (typeof item === "string") return item.trim();
      if (isRecord(item)) {
        return pickFirstString(item, [
          "content",
          "description",
          "detail",
          "achievement",
        ]);
      }
      return null;
    })
    .filter((item): item is string => Boolean(item));
};

const extractDatesFromPeriod = (period?: string) => {
  if (!period) return { startDate: undefined, endDate: undefined };
  const matches = period.match(/\d{4}[.\-/]\d{1,2}(?:[.\-/]\d{1,2})?/g);
  if (!matches || matches.length === 0) {
    return { startDate: undefined, endDate: undefined };
  }

  const toIsoDate = (value: string) => {
    const parts = value.split(/[.\-/]/).filter(Boolean);
    const [year, month, day] = parts;
    if (!year || !month) return undefined;
    const paddedMonth = month.padStart(2, "0");
    const paddedDay = (day ?? "01").padStart(2, "0");
    return `${year}-${paddedMonth}-${paddedDay}`;
  };

  const startDate = toIsoDate(matches[0]);
  const endDate = matches[1] ? toIsoDate(matches[1]) : undefined;
  return { startDate, endDate };
};

const deriveLinkLabel = (value: string, index: number) => {
  try {
    const parsed = new URL(value);
    const host = parsed.hostname.replace(/^www\./, "");
    if (host.includes("github")) return "GitHub";
    if (host.includes("linkedin")) return "LinkedIn";
    if (host.includes("notion")) return "Notion";
    if (host.includes("velog")) return "Velog";
    if (host.includes("tistory")) return "Tistory";
    const base = host.split(".")[0];
    if (base) return `${base[0].toUpperCase()}${base.slice(1)}`;
  } catch (error) {
    console.warn("[Evaluate] Failed to parse link label", error);
  }
  return `링크 ${index + 1}`;
};

const mapParsedResumeToSummary = (
  raw: unknown,
): ResumeSummaryData | null => {
  if (!isRecord(raw)) return null;

  const basicInfo = isRecord(raw.basic_info) ? raw.basic_info : null;
  const careers = toRecordArray(raw.careers);
  const activities = toRecordArray(raw.activities);
  const languages = toRecordArray(raw.languages);

  const experiences = careers
    .map((career) => {
      const company =
        pickFirstString(career, ["company_name", "company", "companyName"]) ??
        "";
      const period = pickFirstString(career, ["period", "duration"]) ?? "";
      const { startDate, endDate } = extractDatesFromPeriod(period);
      const title = pickFirstString(career, ["role", "title", "position"]);
      const achievements = parseAchievements(career.achievements);
      const description = achievements.length > 0 ? achievements.join("\n") : undefined;

      if (!company && !period && !title && !description) return null;

      return {
        company,
        period,
        startDate,
        endDate,
        title,
        description,
      };
    })
    .filter(
      (item): item is ResumeExperience => item !== null,
    );

  const certifications = activities
    .map((activity, index) => {
      const name = pickFirstString(activity, [
        "activity_name",
        "name",
        "title",
      ]);
      const date = pickFirstString(activity, ["period", "date"]);
      const type = pickFirstString(activity, [
        "activity_type",
        "type",
        "category",
      ]);
      const content = pickFirstString(activity, [
        "content",
        "description",
        "detail",
      ]);
      if (!name && !date && !type && !content) return null;

      const note = [type, content].filter(Boolean).join(" / ") || undefined;
      return {
        name: name ?? `활동 ${index + 1}`,
        date,
        note,
      };
    })
    .filter(
      (item): item is ResumeCertification => item !== null,
    );

  const languageItems = languages
    .map((language) => {
      const name = pickFirstString(language, [
        "language_name",
        "name",
        "language",
      ]);
      if (!name) return null;
      const level = pickFirstString(language, ["level"]);
      const certification = pickFirstString(language, ["certification"]);
      const acquisitionDate = pickFirstString(language, ["acquisition_date"]);
      const details = [level, certification, acquisitionDate].filter(Boolean);
      return {
        name,
        details: details.length > 0 ? details : undefined,
      };
    })
    .filter(
      (item): item is ResumeLanguage => item !== null,
    );

  const rawLinks = toStringArray(raw.links);
  const links = rawLinks.map((link, index) => ({
    label: deriveLinkLabel(link, index),
    url: link,
  }));

  return {
    name: pickFirstString(basicInfo, ["name"]) ?? "",
    phone: pickFirstString(basicInfo, ["phone"]),
    email: pickFirstString(basicInfo, ["email"]),
    summary: pickFirstString(raw, ["summary", "about", "intro"]),
    experiences,
    skills: toStringArray(raw.skills),
    certifications,
    languages: languageItems,
    links,
  };
};

const mergeResumeSummary = (
  prev: ResumeSummaryData,
  incoming: ResumeSummaryData,
): ResumeSummaryData => {
  const pickString = (value?: string, fallback?: string) =>
    value && value.trim().length > 0 ? value : fallback;
  const pickArray = <T,>(value: T[] | undefined, fallback: T[] | undefined) =>
    value && value.length > 0 ? value : fallback;

  return {
    ...prev,
    name: pickString(incoming.name, prev.name) ?? "",
    phone: pickString(incoming.phone, prev.phone),
    email: pickString(incoming.email, prev.email),
    summary: pickString(incoming.summary, prev.summary),
    experiences: pickArray(incoming.experiences, prev.experiences) ?? [],
    skills: pickArray(incoming.skills, prev.skills) ?? [],
    certifications: pickArray(incoming.certifications, prev.certifications) ?? [],
    languages: pickArray(incoming.languages, prev.languages) ?? [],
    links: pickArray(incoming.links, prev.links) ?? [],
  };
};

export default function EvaluatePage() {
  const [mode, setMode] = useState<ViewState>("loading");
  const [html, setHtml] = useState("");
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState("");
  const [resumePath, setResumePath] = useState<string | null>(null);
  const [jdText, setJdText] = useState<string | null>(null);
  const [matchingData, setMatchingData] = useState<Record<string, unknown> | null>(null);
  const [isSavedJob, setIsSavedJob] = useState(false);
  const [selectedJob, setSelectedJob] = useState<Record<string, unknown> | null>(null);
  const [resumeSummaryState, setResumeSummaryState] = useState<ResumeSummaryData>(() => {
    if (typeof window !== "undefined") {
      const session = window.sessionStorage;
      const raw = session.getItem("resume_summary");
      const storedPath = session.getItem("resume_summary_path");
      const sessionResume = session.getItem("resume_path");
      if (raw && (!storedPath || storedPath === sessionResume)) {
        try {
          const parsed = JSON.parse(raw);
          if (isRecord(parsed)) {
            return {
              name: toStringValue(parsed.name) ?? "",
              phone: toStringValue(parsed.phone),
              email: toStringValue(parsed.email),
              summary: toStringValue(parsed.summary),
              experiences: Array.isArray(parsed.experiences)
                ? (parsed.experiences as ResumeSummaryData["experiences"])
                : [],
              skills: Array.isArray(parsed.skills)
                ? (parsed.skills as string[])
                : [],
              certifications: Array.isArray(parsed.certifications)
                ? (parsed.certifications as ResumeSummaryData["certifications"])
                : [],
              languages: Array.isArray(parsed.languages)
                ? (parsed.languages as ResumeSummaryData["languages"])
                : [],
              links: Array.isArray(parsed.links)
                ? (parsed.links as ResumeSummaryData["links"])
                : [],
            };
          }
        } catch (error) {
          console.warn("[Evaluate] Failed to parse stored resume summary", error);
        }
      }
    }
    return defaultResumeSummary;
  });

  const normalizeWhitespace = useCallback(
    (value: string) => value.replace(/\s+/g, " ").trim(),
    [],
  );

  const extractJobUrl = useCallback(
    (job: Record<string, unknown>) => pickFirstString(job, ["job_url"]),
    [],
  );

  const extractJobDescription = useCallback(
    (job: Record<string, unknown>) => pickFirstString(job, ["JD"]),
    [],
  );

  // Remove repeated recommendations that share the same link or JD text.
  const deduplicateJobs = useCallback(
    (jobs: Record<string, unknown>[]) => {
      const seenUrls = new Set<string>();
      const seenJds = new Set<string>();

      return jobs.filter((job) => {
        const normalizedUrl = extractJobUrl(job)?.trim().toLowerCase();
        const jobDescription = extractJobDescription(job);
        const normalizedJd = jobDescription
          ? normalizeWhitespace(jobDescription).toLowerCase()
          : undefined;

        if (normalizedUrl && seenUrls.has(normalizedUrl)) {
          return false;
        }
        if (normalizedJd && seenJds.has(normalizedJd)) {
          return false;
        }

        if (normalizedUrl) seenUrls.add(normalizedUrl);
        if (normalizedJd) seenJds.add(normalizedJd);
        return true;
      });
    },
    [extractJobDescription, extractJobUrl, normalizeWhitespace],
  );

  const extractHeadingFromMarkdown = useCallback((markdown?: string) => {
    if (!markdown) return undefined;
    const lines = markdown.split(/\r?\n/);
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      const match = trimmed.match(/^#+\s*(.+)$/);
      if (match?.[1]) {
        return match[1].trim();
      }
      // 첫 줄이 텍스트라면 그 자체를 제목으로 활용
      return trimmed;
    }
    return undefined;
  }, []);

  const deriveJobTitle = useCallback(
    (
      job: Record<string, unknown> | null | undefined,
      fallbackIndex?: number,
    ) => {
      const heading = extractHeadingFromMarkdown(pickFirstString(job, ["JD"]));
      const titleCandidate =
        pickFirstString(job, ["job_title", "title", "position", "role"]) ??
        heading;
      if (titleCandidate) return titleCandidate;

      const companyCandidate = pickFirstString(job, [
        "company",
        "name",
        "organization",
      ]);
      if (companyCandidate) return `${companyCandidate} 채용`;
      if (fallbackIndex !== undefined) return "채용 공고";
      return "채용 공고";
    },
    [extractHeadingFromMarkdown],
  );

  const persistSelectedJobContext = useCallback(
    (
      job: Record<string, unknown> | null | undefined,
      fallbackJd?: string | null,
    ) => {
      if (typeof window === "undefined") return;
      if (!job) {
        window.sessionStorage.removeItem("selected_job_context");
        return;
      }

      const title = deriveJobTitle(job);
      const company =
        pickFirstString(job, ["company", "name", "organization"]) ??
        pickFirstString(matchingData, ["company", "name", "organization"]) ??
        "";
      const jd =
        pickFirstString(job, ["JD"]) ??
        fallbackJd ??
        jdText ??
        "";
      const jobUrl = extractJobUrl(job) ?? "";
      const matchScore =
        pickFirstNumber(job, ["match_score", "match_percentage", "score"]) ??
        pickFirstNumber(matchingData, ["match_score", "score"]);
      const matchLabelValue =
        formatMatchLabel(matchScore) ??
        pickFirstString(job, ["match", "score_label", "match_label"]) ??
        pickFirstString(matchingData, ["match", "score_label", "match_label"]);
      const locationValue =
        pickFirstString(job, ["location", "job_location", "city", "country"]) ??
        pickFirstString(matchingData, ["location", "job_location"]);
      const employmentValue =
        pickFirstString(job, ["employment_type", "job_type", "type"]) ??
        pickFirstString(matchingData, ["employment_type", "job_type"]);
      const remoteValue = resolveRemoteLabel(job) ?? resolveRemoteLabel(matchingData);

      const payload = {
        title,
        company,
        jd,
        jobUrl,
        matchLabel: matchLabelValue,
        location: locationValue,
        employment: employmentValue,
        remote: remoteValue,
        raw: job,
      };

      try {
        window.sessionStorage.setItem("selected_job_context", JSON.stringify(payload));
      } catch (error) {
        console.warn("[Evaluate] Failed to persist selected job context", error);
      }
    },
    [deriveJobTitle, extractJobUrl, jdText, matchingData],
  );

  const transformMatchingResponse = useCallback(
    (response: unknown) => {
      if (!isRecord(response)) {
        return { record: null, jdText: null, html: "" };
      }

      const raw = response as Record<string, unknown>;
      const rawRecommendations = toRecordArray(raw.recommendations);
      const sortedRecommendations = rawRecommendations
        .map((item, index) => ({ item, index }))
        .sort((a, b) => {
          const aScore =
            pickFirstNumber(a.item, ["match_score", "match_percentage", "score"]) ??
            0;
          const bScore =
            pickFirstNumber(b.item, ["match_score", "match_percentage", "score"]) ??
            0;
          if (bScore === aScore) {
            return a.index - b.index;
          }
          return bScore - aScore;
        })
        .map((entry) => entry.item);

      const uniqueRecommendations = deduplicateJobs(sortedRecommendations);

      const primaryCandidate = isRecord(raw.primary)
        ? raw.primary
        : uniqueRecommendations[0] ?? null;

      const record: Record<string, unknown> = {
        ...raw,
        recommendations: uniqueRecommendations,
        primary: primaryCandidate ?? undefined,
      };

      const firstJdText =
        uniqueRecommendations
          .map((item) => toStringValue(item.JD))
          .find(Boolean) ??
        pickFirstString(primaryCandidate, ["JD"]) ??
        toStringValue(raw.output) ??
        null;
      const html = toStringValue(raw.output) ?? "";

      return { record, jdText: firstJdText, html };
    },
    [deduplicateJobs],
  );

  const ensureEssentialData = useCallback(() => {
    if (resumePath) return true;

    if (typeof window === "undefined") {
      return Boolean(resumePath && jdText);
    }

    const session = window.sessionStorage;
    const sessionResume = session.getItem("resume_path");
    const sessionJd = session.getItem("jd_text");

    if (sessionResume) setResumePath(sessionResume);
    if (sessionJd) setJdText(sessionJd);

    return Boolean(sessionResume);
  }, [jdText, resumePath]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const session = window.sessionStorage;
      const sessionResume = session.getItem("resume_path");
      const sessionJd = session.getItem("jd_text");
      const sessionMatchingResume = session.getItem("matching_resume_path");
      const storedMatch = parseStoredMatchingData(session.getItem("matching_result"));

      setResumePath(sessionResume);
      setJdText(sessionJd);

      if (storedMatch && sessionResume && sessionMatchingResume === sessionResume) {
        const { record, jdText: storedJd, html: storedHtml } =
          transformMatchingResponse(storedMatch);
        setMatchingData(record);
        if (storedJd) setJdText(storedJd);
        if (storedHtml) setHtml(storedHtml);
      } else if (
        storedMatch &&
        sessionMatchingResume &&
        sessionResume &&
        sessionMatchingResume !== sessionResume
      ) {
        session.removeItem("matching_result");
        session.removeItem("matching_resume_path");
      }

      const storedResumeSummary = session.getItem("resume_summary");
      const storedSummaryPath = session.getItem("resume_summary_path");
      if (
        storedResumeSummary &&
        (!storedSummaryPath || storedSummaryPath === sessionResume)
      ) {
        try {
          const parsed = JSON.parse(storedResumeSummary);
          if (isRecord(parsed)) {
            setResumeSummaryState((prev) => ({
              ...prev,
              ...parsed,
            }));
          }
        } catch (error) {
          console.warn("[Evaluate] Failed to hydrate resume summary from session", error);
        }
      }
    }
  }, [transformMatchingResponse]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const session = window.sessionStorage;
    const currentResume = resumePath;
    if (!currentResume) return;

    const storedSummary = session.getItem("resume_summary");
    const storedSummaryPath = session.getItem("resume_summary_path");
    if (storedSummary && storedSummaryPath === currentResume) {
      return;
    }

    const controller = new AbortController();

    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/parse-resume`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resume_path: currentResume }),
      signal: controller.signal,
    })
      .then(async (res) => {
        const text = await res.text();
        let parsed: unknown = null;
        try {
          parsed = text ? JSON.parse(text) : null;
        } catch (parseErr) {
          console.warn("[Evaluate] Failed to parse resume summary", parseErr);
        }
        if (!res.ok) {
          const detail =
            (isRecord(parsed) && (parsed.detail as string)) ||
            (isRecord(parsed) && (parsed.error as string)) ||
            text ||
            "서버 오류";
          throw new Error(detail);
        }
        if (!parsed) {
          throw new Error("서버 응답을 이해할 수 없습니다.");
        }
        return parsed;
      })
      .then((data) => {
        const mapped = mapParsedResumeToSummary(data);
        if (!mapped) return;
        const latestSummaryPath = session.getItem("resume_summary_path");
        if (latestSummaryPath === currentResume) {
          return;
        }
        setResumeSummaryState((prev) => {
          const base =
            storedSummaryPath && storedSummaryPath !== currentResume
              ? defaultResumeSummary
              : prev;
          const merged = mergeResumeSummary(base, mapped);
          session.setItem("resume_summary", JSON.stringify(merged));
          session.setItem("resume_summary_path", currentResume);
          return merged;
        });
      })
      .catch((err: unknown) => {
        if (err instanceof Error && err.name === "AbortError") {
          return;
        }
        console.warn(
          "[Evaluate] Failed to fetch resume summary",
          err instanceof Error ? err.message : err,
        );
      });

    return () => {
      controller.abort();
    };
  }, [resumePath]);

  useEffect(() => {
    if (mode !== "loading") return;

    const currentResume =
      resumePath ??
      (typeof window !== "undefined"
        ? window.sessionStorage.getItem("resume_path")
        : null);

    // If we already have cached data for the same resume, reuse without re-fetch.
    if (typeof window !== "undefined" && currentResume) {
      const cachedResume = window.sessionStorage.getItem("matching_resume_path");
      const cachedRaw = window.sessionStorage.getItem("matching_result");
      const cachedMatch = parseStoredMatchingData(cachedRaw);
      if (cachedMatch && cachedResume === currentResume) {
        const { record, jdText: cachedJd, html: cachedHtml } =
          transformMatchingResponse(cachedMatch);
        setMatchingData(record);
        if (cachedJd) setJdText(cachedJd);
        if (cachedHtml) setHtml(cachedHtml);
        setMode("result");
        return;
      }
    }

    if (!ensureEssentialData()) {
      setError(
        "이전 단계 정보가 누락되었습니다. 선호도 입력 페이지에서 다시 진행해주세요.",
      );
      setMode("error");
      return;
    }

    setError("");
    setHtml("");
    setProgress(0);

    const steps = [12, 28, 46, 63, 82, 95];

    let stepIdx = 0;
    const interval = window.setInterval(() => {
      if (stepIdx < steps.length) {
        setProgress(steps[stepIdx]);
        stepIdx += 1;
      }
    }, 1200);

    if (!currentResume) {
      clearInterval(interval);
      setError(
        "이력서 정보가 없습니다. 이전 단계에서 업로드를 완료해주세요.",
      );
      setMode("error");
      return () => {};
    }

    const controller = new AbortController();

    const handleSuccess = (data: Record<string, unknown>) => {
      const { record, jdText: incomingJd, html: incomingHtml } =
        transformMatchingResponse(data);

      if (record) {
        setMatchingData(record);
        if (typeof window !== "undefined") {
          window.sessionStorage.setItem("matching_result", JSON.stringify(record));
          window.sessionStorage.setItem("matching_resume_path", currentResume);
        }
      }
      if (incomingJd) {
        setJdText(incomingJd);
        if (typeof window !== "undefined") {
          window.sessionStorage.setItem("jd_text", incomingJd);
        }
      }
      if (incomingHtml) {
        setHtml(incomingHtml);
      }

      setProgress(100);
      setMode("result");
    };

    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/matching`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        resume_path: currentResume,
      }),
      signal: controller.signal,
    })
      .then(async (res) => {
        const text = await res.text();
        let parsed: Record<string, unknown> | null = null;
        try {
          parsed = text ? (JSON.parse(text) as Record<string, unknown>) : null;
        } catch (parseErr) {
          console.warn("[Evaluate] Failed to parse matching response", parseErr);
        }
        if (!res.ok) {
          const detail =
            (parsed && (parsed.detail as string)) ||
            (parsed && (parsed.error as string)) ||
            text ||
            "서버 오류";
          throw new Error(detail);
        }
        if (!parsed) {
          throw new Error("서버 응답을 이해할 수 없습니다.");
        }
        return parsed;
      })
      .then((data) => {
        handleSuccess(data);
      })
      .catch((err: unknown) => {
        if (err instanceof Error && err.name === "AbortError") {
          return;
        }
        setError(
          err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다.",
        );
        setMode("error");
      })
      .finally(() => {
        clearInterval(interval);
      });

    return () => {
      clearInterval(interval);
      controller.abort();
    };
  }, [ensureEssentialData, jdText, mode, resumePath, transformMatchingResponse]);

  const primaryRecommendation = useMemo(() => {
    if (!matchingData) return null;
    const record = matchingData;
    const recommendations = toRecordArray(record["recommendations"]);
    if (recommendations.length > 0) return recommendations[0];
    return null;
  }, [matchingData]);

  useEffect(() => {
    if (primaryRecommendation) {
      setSelectedJob(primaryRecommendation);
    }
  }, [primaryRecommendation]);

  const similarJobs = useMemo(() => {
    if (!matchingData) return [];
    const record = matchingData;
    const aggregated = toRecordArray(record["recommendations"]);
    const sorted = aggregated
      .map((item, index) => ({ item, index }))
      .sort((a, b) => {
        const aScore =
          pickFirstNumber(a.item, ["match_score", "match_percentage", "score"]) ??
          0;
        const bScore =
          pickFirstNumber(b.item, ["match_score", "match_percentage", "score"]) ??
          0;
        if (bScore === aScore) {
          return a.index - b.index;
        }
        return bScore - aScore;
      })
      .map((entry) => entry.item);

    const effectivePrimary = selectedJob ?? primaryRecommendation;
    const primaryUrl = effectivePrimary ? extractJobUrl(effectivePrimary) : undefined;

    const unique = deduplicateJobs(sorted);

    return unique.filter((item) => {
      if (item === effectivePrimary) return false;
      if (primaryUrl) {
        const url = extractJobUrl(item);
        if (url && url === primaryUrl) return false;
      }
      return true;
    });
  }, [deduplicateJobs, extractJobUrl, matchingData, primaryRecommendation, selectedJob]);

  const effectivePrimary = selectedJob ?? primaryRecommendation ?? matchingData;

  const jobTitle = deriveJobTitle(effectivePrimary);

  const companyName =
    pickFirstString(effectivePrimary, ["company"]) ??
    pickFirstString(matchingData, ["company"]) ??
    "회사명";

  const locationLabel =
    pickFirstString(effectivePrimary, [
      "location",
      "job_location",
      "city",
      "country",
    ]) ?? pickFirstString(matchingData, ["location", "job_location"]);

  const employmentLabel =
    pickFirstString(effectivePrimary, [
      "employment_type",
      "job_type",
      "type",
    ]) ?? pickFirstString(matchingData, ["employment_type", "job_type"]);

  const remoteLabel =
    resolveRemoteLabel(effectivePrimary) ??
    resolveRemoteLabel(matchingData);

  const matchNumber =
    pickFirstNumber(effectivePrimary, [
      "match_score",
      "match_percentage",
      "score",
    ]) ?? pickFirstNumber(matchingData, ["match_score", "score"]);

  const matchLabel =
    formatMatchLabel(matchNumber) ??
    pickFirstString(effectivePrimary, ["match", "score_label", "match_label"]) ??
    pickFirstString(matchingData, ["match", "score_label", "match_label"]);

  const jobUrl = primaryRecommendation
    ? extractJobUrl(effectivePrimary ?? {})
    : extractJobUrl(matchingData ?? {});

  const logoUrl =
    pickFirstString(effectivePrimary, [
      "logo",
      "company_logo",
      "image",
      "logo_url",
    ]) ?? pickFirstString(matchingData, ["logo", "company_logo"]);

  const jobDescriptionText =
    pickFirstString(effectivePrimary, ["JD"]) ??
    pickFirstString(matchingData, ["JD"]) ??
    jdText ??
    undefined;

  // Persist the currently selected job so the editor can reuse its context.
  useEffect(() => {
    persistSelectedJobContext(effectivePrimary, jobDescriptionText ?? null);
  }, [effectivePrimary, jobDescriptionText, persistSelectedJobContext]);

  const analysisText =
    pickFirstString(effectivePrimary, ["analysis", "notes", "output"]) ??
    pickFirstString(matchingData, ["output"]);

  const jobDescriptionHtml = useMemo(() => {
    if (!jobDescriptionText) return "";
    const parsed = marked.parse(jobDescriptionText);
    const parsedHtml = typeof parsed === "string" ? parsed : "";
    return DOMPurify.sanitize(parsedHtml);
  }, [jobDescriptionText]);

  const analysisHtml = useMemo(() => {
    if (analysisText) {
      const parsed = marked.parse(analysisText);
      const parsedHtml = typeof parsed === "string" ? parsed : "";
      return DOMPurify.sanitize(parsedHtml);
    }
    if (html) {
      return DOMPurify.sanitize(html);
    }
    return "";
  }, [analysisText, html]);

  const metaInformation = [locationLabel, employmentLabel, remoteLabel].filter(
    (value): value is string => Boolean(value),
  );

  const contentWidthClass = "max-w-[90rem]";

  const renderLoading = () => (
    <section className="flex min-h-[60vh] items-center justify-center">
      <div className="w-full max-w-xl rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="flex flex-col items-center gap-5">
          <div className="flex items-center gap-3">
            <div
              className="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-[rgb(96,150,222)]"
              aria-hidden="true"
            />
            <p className="text-lg font-semibold text-slate-900">로딩중입니다</p>
          </div>
          <div
            className="w-full rounded-full bg-slate-100"
            role="progressbar"
            aria-valuenow={progress}
            aria-valuemin={0}
            aria-valuemax={100}
          >
            <div
              className="h-3 rounded-full bg-[rgb(96,150,222)] transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-xs text-slate-500">{progress}%</p>
        </div>
      </div>
    </section>
  );

  const renderError = () => (
    <section className="space-y-8">
      <div className="rounded-3xl border border-rose-200 bg-white p-10 shadow-sm">
        <h2 className="text-xl font-semibold text-rose-600">오류가 발생했어요</h2>
        <p className="mt-3 text-sm text-rose-500">
          {error ||
            "현재 분석을 진행할 수 없습니다. 잠시 후 다시 시도해주세요."}
        </p>
        <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-end">
          <Link
            href="/preferences"
            className="inline-flex items-center justify-center rounded-full border border-slate-200 px-6 py-3 text-sm font-semibold text-slate-600 transition hover:bg-slate-50"
          >
            이전 화면으로
          </Link>
          <Link
            href="/"
            className="inline-flex items-center justify-center rounded-full bg-[rgb(96,150,222)] px-6 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-[rgb(86,140,212)]"
          >
            메인으로 돌아가기
          </Link>
        </div>
      </div>
    </section>
  );

  const renderResult = () => {
    const displayedSimilarJobs = similarJobs.slice(0, 3);
    const resumeSummary = resumeSummaryState;
    const similarCards = displayedSimilarJobs.map((job, index) => {
      const title = deriveJobTitle(job, index);
      const company = pickFirstString(job, ["company"]) ?? companyName;
      const location =
        pickFirstString(job, ["location"]) ?? locationLabel;
      const matchScore =
        pickFirstNumber(job, ["match_score", "match_percentage", "score"]) ??
        pickFirstNumber(matchingData, ["match_score", "score"]);
      const matchBadge =
        formatMatchLabel(matchScore) ??
        pickFirstString(job, ["match", "score_label", "match_label"]);

      const cardContent = (
        <>
          <div className="space-y-2">
            <h4 className="text-lg font-semibold text-slate-900">{title}</h4>
            <p className="text-sm font-medium text-slate-600">{company}</p>
            {location && (
              <p className="text-sm text-slate-400">{location}</p>
            )}
          </div>
          <div className="mt-4 flex items-center justify-between">
            {matchBadge ? (
              <span className="inline-flex items-center rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-600">
                {matchBadge}
              </span>
            ) : (
              <span className="text-xs text-slate-300">Match 정보 없음</span>
            )}
            <span className="ml-auto inline-flex items-center gap-1 text-xs font-semibold text-[rgb(96,150,222)]">
              View
            </span>
          </div>
        </>
      );

      return (
        <button
          key={`${title}-${company}-${index}`}
          type="button"
          onClick={() => {
            setSelectedJob(job);
            persistSelectedJobContext(job);
          }}
          className="flex min-w-[240px] max-w-[260px] flex-col justify-between rounded-2xl border border-slate-200 bg-white p-6 text-left shadow-sm transition hover:-translate-y-1 hover:shadow-md focus-visible:-translate-y-1 focus-visible:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[rgba(96,150,222,0.5)]"
        >
          {cardContent}
        </button>
      );
    });

    const hasSimilarJobs = similarCards.length > 0;

    return (
      <section className="space-y-10">
        <div className="grid gap-6 lg:grid-cols-[minmax(0,4fr)_minmax(0,3fr)]">
          <ResumeSummaryView
            summary={resumeSummary}
            editable
            onChange={(next) => {
              setResumeSummaryState(next);
              if (typeof window !== "undefined") {
                window.sessionStorage.setItem(
                  "resume_summary",
                  JSON.stringify(next),
                );
                const currentResume =
                  resumePath ?? window.sessionStorage.getItem("resume_path");
                if (currentResume) {
                  window.sessionStorage.setItem(
                    "resume_summary_path",
                    currentResume,
                  );
                }
              }
            }}
          />

          <div className="space-y-6">
            <div className="space-y-4">
              <h3 className="text-2xl font-semibold text-slate-900">추천 공고</h3>
              <div className="rounded-3xl border border-slate-200 bg-white p-10 shadow-sm">
                <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
                  <div className="space-y-3">
                    {logoUrl && (
                      <div className="flex h-12 w-12 items-center justify-center overflow-hidden rounded-full border border-slate-200 bg-white">
                        <Image
                          src={logoUrl}
                          alt={`${companyName} logo`}
                          width={48}
                          height={48}
                          className="h-full w-full object-contain p-1"
                          unoptimized
                        />
                      </div>
                    )}
                    <h2 className="text-2xl font-semibold text-slate-900">
                      {jobTitle}
                    </h2>
                    <p className="text-sm font-medium text-slate-600">
                      {companyName}
                    </p>
                    {metaInformation.length > 0 && (
                      <p className="flex flex-wrap gap-2 text-sm text-slate-400">
                        {metaInformation.map((meta) => (
                          <span key={meta}>{meta}</span>
                        ))}
                      </p>
                    )}
                  </div>
                  <div className="flex flex-col items-end gap-3">
                    {matchLabel && (
                      <span className="inline-flex items-center rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-600">
                        {matchLabel}
                      </span>
                    )}
                    
                  </div>
                </div>

              <div className="mt-6 space-y-8">
                {jobDescriptionHtml ? (
                  <section className="space-y-2">
                    <div
                      className="prose max-w-none text-xs leading-relaxed text-slate-700 sm:text-sm"
                      dangerouslySetInnerHTML={{ __html: jobDescriptionHtml }}
                    />
                  </section>
                ) : (
                  <p className="text-sm text-slate-400">
                    추천 공고 설명을 불러오지 못했습니다.
                  </p>
                )}

                {analysisHtml && (
                  <section className="space-y-3">
                    <h4 className="text-base font-semibold text-slate-900">
                      자격 요건
                    </h4>
                    <div
                      className="prose prose-sm max-w-none text-xs leading-relaxed text-slate-600 sm:text-sm"
                      dangerouslySetInnerHTML={{ __html: analysisHtml }}
                    />
                  </section>
                )}
              </div>

                <div className="mt-8 flex flex-wrap items-center gap-3 lg:justify-end">
                  <button
                    type="button"
                    onClick={() => {
                      if (jobUrl && typeof window !== "undefined") {
                        window.open(jobUrl, "_blank", "noopener,noreferrer");
                      }
                    }}
                    disabled={!jobUrl}
                    className={`inline-flex h-12 w-12 items-center justify-center rounded-2xl transition ${
                      jobUrl
                        ? "bg-[rgba(96,150,222,0.1)] text-[rgb(96,150,222)] hover:bg-[rgba(96,150,222,0.18)]"
                        : "cursor-not-allowed bg-slate-200 text-slate-400"
                    }`}
                    aria-label="공고 링크 열기"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      strokeWidth={1.5}
                      stroke="currentColor"
                      className="h-5 w-5"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M13.5 4.5H19.5V10.5M10.5 13.5 19.5 4.5M9 6H6.75C5.645 6 4.5 7.145 4.5 8.25v9c0 1.105 1.145 2.25 2.25 2.25h9c1.105 0 2.25-1.145 2.25-2.25V15"
                      />
                    </svg>
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsSavedJob((prev) => !prev)}
                    className={`inline-flex h-12 w-12 items-center justify-center rounded-2xl transition ${
                      isSavedJob
                        ? "bg-[rgb(96,150,222)] text-white"
                        : "bg-[rgba(96,150,222,0.1)] text-[rgb(96,150,222)] hover:bg-[rgba(96,150,222,0.18)]"
                    }`}
                    aria-pressed={isSavedJob}
                    aria-label="관심 공고 저장"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="currentColor"
                      className="h-5 w-5"
                    >
                      <path d="M6.75 3A1.75 1.75 0 005 4.75v15.19a.5.5 0 00.77.416L12 17.5l6.23 2.856a.5.5 0 00.77-.415V4.75A1.75 1.75 0 0017.25 3H6.75z" />
                    </svg>
                  </button>
                  <Link
                    href="/editor"
                    onClick={() =>
                      persistSelectedJobContext(effectivePrimary, jobDescriptionText ?? null)
                    }
                    className="inline-flex items-center justify-center rounded-xl bg-[rgb(96,150,222)] px-6 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-[rgb(86,140,212)]"
                  >
                    공고 맞춤 이력서 수정
                  </Link>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <h4 className="text-lg font-semibold text-slate-900">
                이런 공고도 있어요.
              </h4>
              {hasSimilarJobs ? (
                <div className="flex gap-4 overflow-x-auto pb-2">
                  {similarCards}
                </div>
              ) : (
                <p className="text-sm text-slate-400">
                  아직 추천할 추가 공고가 없습니다. 선호 조건을 더 입력해보세요.
                </p>
              )}
            </div>
          </div>
        </div>
      </section>
    );
  };

  return (
    <div className="min-h-screen bg-[#1f1f1f]">
      <AppHeader />

      <main className="min-h-[calc(100vh-4rem)] bg-[#f6f7fb]">
        <div className={`mx-auto ${contentWidthClass} px-4 py-12 sm:px-8`}>
          {mode === "loading" && renderLoading()}
          {mode === "error" && renderError()}
          {mode === "result" && renderResult()}
        </div>
      </main>
    </div>
  );
}
