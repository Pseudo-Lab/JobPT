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
import ResumeSummaryView, { ResumeSummaryData } from "@/components/evaluate/ResumeSummaryView";
import {
  ensureMockSessionData,
  isMockEnabled,
  MOCK_EVALUATE_HTML,
  MOCK_MATCHING_RESPONSE,
  MOCK_RESUME_PATH,
  parseMatchingData,
} from "@/lib/mockData";
import AppHeader from "@/components/common/AppHeader";

type ViewState = "loading" | "result" | "error";

export default function EvaluatePage() {
  const [mode, setMode] = useState<ViewState>("loading");
  const [html, setHtml] = useState("");
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState("");
  const [resumePath, setResumePath] = useState<string | null>(null);
  const [jdText, setJdText] = useState<string | null>(null);
  const [matchingData, setMatchingData] = useState<Record<string, unknown> | null>(null);
  const [isSavedJob, setIsSavedJob] = useState(false);

  const defaultResumeSummary: ResumeSummaryData = {
    name: "김길동",
    phone: "010-0000-0000",
    email: "email@gmail.com",
    summary:
      "안녕하세요, 서비스 기획자 김길동입니다. 간단한 자기소개가 이곳에 들어갑니다. 간단한 자기소개가 이곳에 들어갑니다. 간단한 자기소개가 이곳에 들어갑니다.",
    experiences: [
      {
        company: "회사명",
        period: "0000.00 ~ 재직중 (0년 00개월)",
        title: "담당한 역할 타이틀",
        description:
          "담당한 역할과 업무 등에 대한 내용이 이곳에 들어갑니다. 담당한 역할과 업무 등에 대한 내용이 이곳에 들어갑니다. 담당한 역할과 업무 등에 대한 내용이 이곳에 들어갑니다.",
        logoUrl: "/logo/main_logo.png",
      },
      {
        company: "회사명",
        period: "0000.00 ~ 0000.00",
        title: "담당한 역할 타이틀",
        description:
          "담당한 역할과 업무 등에 대한 내용이 이곳에 들어갑니다. 담당한 역할과 업무 등에 대한 내용이 이곳에 들어갑니다. 담당한 역할과 업무 등에 대한 내용이 이곳에 들어갑니다.",
      },
    ],
    skills: ["Python", "Figma", "React", "TypeScript", "Next.js", "Git"],
    certifications: [
      { name: "자격증 이름", date: "0000.00", note: "취득" },
      { name: "수상내역", date: "0000.00", note: "수상" },
    ],
    languages: [
      {
        name: "영어",
        details: ["OPIc IM1 (Intermediate Mid)", "TOEIC 990"],
      },
      {
        name: "중국어",
        details: ["HSK 6급"],
      },
    ],
    links: [{ label: "https://github.com/gildong", url: "https://github.com/gildong" }],
  };

  const extractHeadingFromMarkdown = (markdown?: string) => {
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
  };

  const deriveJobTitle = (
    job: Record<string, unknown> | null | undefined,
    fallbackIndex?: number,
  ) => {
    const heading = extractHeadingFromMarkdown(
      pickFirstString(job, ["JD", "jd", "description"]),
    );
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
  };

  const transformMatchingResponse = (response: unknown) => {
    if (!isRecord(response)) {
      return { record: null, jdText: null, html: "" };
    }

    const raw = response as Record<string, unknown>;
    const toList = (fields: string[]) => {
      for (const field of fields) {
        const value = raw[field];
        if (Array.isArray(value)) return value;
        if (value !== undefined && value !== null) return [value];
      }
      return [];
    };

    const jdList = toList(["JD", "jd", "job_description"]);
    const scoreList = toList(["match_score", "match_percentage", "score"]);
    const urlList = toList([
      "JD_url",
      "jd_url",
      "job_url",
      "job_urls",
      "url",
      "urls",
      "link",
    ]);
    const nameList = toList(["name", "company", "company_name"]);
    const jobTitleList = toList(["job_title", "title", "position", "role"]);

    const parsedRecommendations = jdList
      .map((jdEntry, index) => {
        const jdTextCandidate = toStringValue(jdEntry);
        const companyCandidate =
          toStringValue(nameList[index]) ??
          toStringValue(raw.company) ??
          toStringValue(raw.name);
        const jobUrlCandidate =
          toStringValue(urlList[index]) ??
          toStringValue(raw.job_url) ??
          toStringValue(raw.url) ??
          toStringValue(raw.JD_url);
        const jobTitleCandidate =
          toStringValue(jobTitleList[index]) ??
          pickFirstString(raw, ["job_title", "title", "position", "role"]) ??
          extractHeadingFromMarkdown(jdTextCandidate);
        const scoreCandidate =
          typeof scoreList[index] === "number"
            ? (scoreList[index] as number)
            : pickFirstNumber(scoreList[index], ["match_score", "score"]);

        if (!jdTextCandidate && !companyCandidate && !jobUrlCandidate) {
          return null;
        }

        const base: Record<string, unknown> = {
          JD: jdTextCandidate,
          jd: jdTextCandidate,
          jd_url: jobUrlCandidate,
          job_url: jobUrlCandidate,
          company: companyCandidate,
          name: companyCandidate,
          match_score: scoreCandidate,
        };

        if (jobTitleCandidate) {
          base.job_title = jobTitleCandidate;
          base.title = jobTitleCandidate;
        }

        return base;
      })
      .filter((item): item is Record<string, unknown> => item !== null);

    const rawRecommendations = toRecordArray(raw.recommendations);
    const recommendations =
      rawRecommendations.length > 0 ? rawRecommendations : parsedRecommendations;

    const sortedRecommendations = recommendations
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

    const record: Record<string, unknown> = {
      ...raw,
      recommendations: sortedRecommendations,
    };

    if (isRecord(raw.primary)) {
      record.primary = raw.primary;
    } else if (sortedRecommendations[0]) {
      record.primary = sortedRecommendations[0];
    }

    const firstJdText =
      jdList.map((item) => toStringValue(item)).find(Boolean) ??
      sortedRecommendations
        .map((item) => toStringValue(item.JD) ?? toStringValue(item.jd))
        .find(Boolean) ??
      null;
    const html = toStringValue(raw.output) ?? "";

    return { record, jdText: firstJdText, html };
  };

  const ensureEssentialData = useCallback(() => {
    if (resumePath) return true;

    if (isMockEnabled) {
      ensureMockSessionData();
    }

    if (typeof window === "undefined") {
      return Boolean(resumePath && jdText);
    }

    const session = window.sessionStorage;
    let sessionResume = session.getItem("resume_path");
    let sessionJd = session.getItem("jd_text");

    if (!sessionResume && isMockEnabled) {
      sessionResume = MOCK_RESUME_PATH;
      session.setItem("resume_path", sessionResume);
    }
    if (!sessionJd && isMockEnabled) {
      sessionJd = MOCK_MATCHING_RESPONSE.JD;
      session.setItem("jd_text", sessionJd);
    }

    if (sessionResume) setResumePath(sessionResume);
    if (sessionJd) setJdText(sessionJd);

    return Boolean(sessionResume);
  }, [jdText, resumePath]);

  useEffect(() => {
    if (isMockEnabled) {
      ensureMockSessionData();
    }

    if (typeof window !== "undefined") {
      const session = window.sessionStorage;
      const sessionResume = session.getItem("resume_path");
      const sessionJd = session.getItem("jd_text");
      const storedMatch = parseMatchingData(session.getItem("matching_result"));

      setResumePath(sessionResume ?? (isMockEnabled ? MOCK_RESUME_PATH : null));
      setJdText(sessionJd ?? (isMockEnabled ? MOCK_MATCHING_RESPONSE.JD : null));
      setMatchingData(
        storedMatch ?? (isMockEnabled ? MOCK_MATCHING_RESPONSE : null),
      );

    }
  }, []);

  useEffect(() => {
    if (mode !== "loading") return;

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

    const currentResume =
      resumePath ??
      (typeof window !== "undefined"
        ? window.sessionStorage.getItem("resume_path")
        : null);
    const currentJd =
      jdText ??
      (typeof window !== "undefined"
        ? window.sessionStorage.getItem("jd_text")
        : null);

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
      }
      if (incomingJd) {
        setJdText(incomingJd);
      }
      if (incomingHtml) {
        setHtml(incomingHtml);
      }

      setProgress(100);
      setMode("result");
    };

    if (isMockEnabled) {
      const timer = window.setTimeout(() => {
        handleSuccess({
          ...(MOCK_MATCHING_RESPONSE as unknown as Record<string, unknown>),
          output: MOCK_EVALUATE_HTML,
        });
      }, 1200);

      return () => {
        clearInterval(interval);
        window.clearTimeout(timer);
      };
    }

    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/matching`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        resume_path: currentResume,
        jd_text: currentJd,
      }),
      signal: controller.signal,
    })
      .then(async (res) => {
        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          throw new Error(data.detail || data.error || "서버 오류");
        }
        return res.json();
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
  }, [ensureEssentialData, jdText, mode, resumePath]);

  const primaryRecommendation = useMemo(() => {
    if (!matchingData) return null;
    const record = matchingData;
    const candidateSources: unknown[] = [
      record["recommendations"],
      record["primary"],
      record["recommended"],
      record["recommended_job"],
      record["job"],
    ];
    for (const source of candidateSources) {
      const list = toRecordArray(source);
      if (list.length > 0) return list[0];
    }
    return record;
  }, [matchingData]);

  const similarJobs = useMemo(() => {
    if (!matchingData) return [];
    const record = matchingData;
    const getJobUrl = (job: Record<string, unknown>) =>
      pickFirstString(job, ["url", "link", "job_url", "jd_url", "JD_url"]);
    const aggregated = [
      ...toRecordArray(record["similar_jobs"]),
      ...toRecordArray(record["alternatives"]),
      ...toRecordArray(record["related"]),
      ...toRecordArray(record["recommendations"]),
    ];
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

    const primaryUrl = primaryRecommendation
      ? getJobUrl(primaryRecommendation)
      : undefined;

    return sorted.filter((item) => {
      if (item === primaryRecommendation) return false;
      if (primaryUrl) {
        const url = getJobUrl(item);
        if (url && url === primaryUrl) return false;
      }
      return true;
    });
  }, [matchingData, primaryRecommendation]);

  const jobTitle = deriveJobTitle(primaryRecommendation ?? matchingData);

  const companyName =
    pickFirstString(primaryRecommendation, ["company", "name", "organization"]) ??
    pickFirstString(matchingData, ["company", "name"]) ??
    "회사명";

  const locationLabel =
    pickFirstString(primaryRecommendation, [
      "location",
      "job_location",
      "city",
      "country",
    ]) ?? pickFirstString(matchingData, ["location", "job_location"]);

  const employmentLabel =
    pickFirstString(primaryRecommendation, [
      "employment_type",
      "job_type",
      "type",
    ]) ?? pickFirstString(matchingData, ["employment_type", "job_type"]);

  const remoteLabel =
    resolveRemoteLabel(primaryRecommendation) ??
    resolveRemoteLabel(matchingData);

  const matchNumber =
    pickFirstNumber(primaryRecommendation, [
      "match_score",
      "match_percentage",
      "score",
    ]) ?? pickFirstNumber(matchingData, ["match_score", "score"]);

  const matchLabel =
    formatMatchLabel(matchNumber) ??
    pickFirstString(primaryRecommendation, ["match", "score_label", "match_label"]) ??
    pickFirstString(matchingData, ["match", "score_label", "match_label"]);

  const jobUrl =
    pickFirstString(primaryRecommendation, ["url", "link", "job_url", "jd_url"]) ??
    pickFirstString(matchingData, ["JD_url", "job_url", "url"]);

  const logoUrl =
    pickFirstString(primaryRecommendation, [
      "logo",
      "company_logo",
      "image",
      "logo_url",
    ]) ?? pickFirstString(matchingData, ["logo", "company_logo"]);

  const jobDescriptionText =
    pickFirstString(primaryRecommendation, [
      "description",
      "summary",
      "JD",
      "jd",
      "details",
      "responsibilities",
    ]) ??
    pickFirstString(matchingData, ["JD", "jd", "description"]) ??
    jdText ??
    undefined;

  const analysisText =
    pickFirstString(primaryRecommendation, ["analysis", "notes", "output"]) ??
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
    const resumeSummary = defaultResumeSummary;
    const similarCards = displayedSimilarJobs.map((job, index) => {
      const title = deriveJobTitle(job, index);
      const company =
        pickFirstString(job, ["company", "name", "organization"]) ??
        companyName;
      const location =
        pickFirstString(job, ["location", "job_location", "city", "country"]) ??
        locationLabel;
      const matchScore =
        pickFirstNumber(job, ["match_score", "match_percentage", "score"]) ??
        pickFirstNumber(matchingData, ["match_score", "score"]);
      const matchBadge =
        formatMatchLabel(matchScore) ??
        pickFirstString(job, ["match", "score_label", "match_label"]);
      const url =
        pickFirstString(job, ["url", "link", "job_url", "jd_url"]) ??
        jobUrl ??
        undefined;

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
            {url ? (
              <span className="inline-flex items-center gap-1 text-xs font-semibold text-[rgb(96,150,222)]">
                상세보기
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={1.5}
                  stroke="currentColor"
                  className="h-4 w-4"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M4.5 12h15m0 0-6-6m6 6-6 6"
                  />
                </svg>
              </span>
            ) : (
              <span className="text-xs text-slate-300">링크 없음</span>
            )}
          </div>
        </>
      );

      if (url) {
        return (
          <a
            key={`${title}-${company}-${index}`}
            href={url}
            target="_blank"
            rel="noreferrer"
            className="flex min-w-[240px] max-w-[260px] flex-col justify-between rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-md focus-visible:-translate-y-1 focus-visible:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[rgba(96,150,222,0.5)]"
          >
            {cardContent}
          </a>
        );
      }

      return (
        <div
          key={`${title}-${company}-${index}`}
          className="flex min-w-[240px] max-w-[260px] flex-col justify-between rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
        >
          {cardContent}
        </div>
      );
    });

    const hasSimilarJobs = similarCards.length > 0;

    return (
      <section className="space-y-10">
        <div className="grid gap-6 lg:grid-cols-[minmax(0,4fr)_minmax(0,3fr)]">
          <ResumeSummaryView summary={resumeSummary} />

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
