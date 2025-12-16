"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  ensureMockSessionData,
  isMockEnabled,
  MOCK_RESUME_PATH,
} from "@/lib/mockData";
import AppHeader from "@/components/common/AppHeader";

type RemotePreference = "yes" | "no";

const SALARY_MIN = 0;
const SALARY_MAX = 200_000_000;
const SALARY_STEP = 5_000_000;

const EMPLOYMENT_OPTIONS = ["정규직", "계약직", "인턴", "프리랜서", "파트타임"];

const formatNumber = (value: number) =>
  new Intl.NumberFormat("ko-KR").format(value);

export default function PreferencesPage() {
  const router = useRouter();
  const [locationInput, setLocationInput] = useState("");
  const [employmentType, setEmploymentType] = useState(EMPLOYMENT_OPTIONS[0]);
  const [remotePreference, setRemotePreference] =
    useState<RemotePreference>("yes");
  const [salary, setSalary] = useState(60_000_000);
  const [position, setPosition] = useState("");
  const [industry, setIndustry] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (isMockEnabled) {
      ensureMockSessionData();
    }

    if (typeof window === "undefined") return;

    const storedPreferences = window.localStorage.getItem("jobpt_preferences");
    if (!storedPreferences) return;

    try {
      const parsed = JSON.parse(storedPreferences) as {
        location?: string;
        employmentType?: string;
        remotePreference?: RemotePreference;
        salary?: number;
        position?: string;
        industry?: string;
      };

      if (parsed.location) setLocationInput(parsed.location);
      if (
        parsed.employmentType &&
        EMPLOYMENT_OPTIONS.includes(parsed.employmentType)
      ) {
        setEmploymentType(parsed.employmentType);
      }
      if (parsed.remotePreference) setRemotePreference(parsed.remotePreference);
      if (typeof parsed.salary === "number") setSalary(parsed.salary);
      if (parsed.position) setPosition(parsed.position);
      if (parsed.industry) setIndustry(parsed.industry);
    } catch (err) {
      console.warn("[PreferencesPage] Failed to parse preferences", err);
    }
  }, []);

  const ensureEssentialData = () => {
    if (isMockEnabled) {
      ensureMockSessionData();
    }

    if (typeof window === "undefined") {
      return false;
    }

    const session = window.sessionStorage;
    let sessionResume = session.getItem("resume_path");

    if (!sessionResume && isMockEnabled) {
      sessionResume = MOCK_RESUME_PATH;
      session.setItem("resume_path", sessionResume);
    }

    return Boolean(sessionResume);
  };

  const persistPreferences = () => {
    if (typeof window === "undefined") return;
    const preferences = {
      location: locationInput,
      employmentType,
      remotePreference,
      salary,
      position,
      industry,
    };
    window.localStorage.setItem(
      "jobpt_preferences",
      JSON.stringify(preferences),
    );
  };

  const proceedToEvaluate = () => {
    if (!ensureEssentialData()) {
      setError("이전 단계 정보가 누락되었습니다. 업로드 단계부터 다시 진행해주세요.");
      return;
    }
    router.push("/evaluate");
  };

  const handleSkip = () => {
    setError("");
    proceedToEvaluate();
  };

  const handleSavePreferences = () => {
    persistPreferences();
    setError("");
    proceedToEvaluate();
  };

  return (
    <div className="min-h-screen bg-[#1f1f1f]">
      <AppHeader />

      <main className="min-h-[calc(100vh-4rem)] bg-[#f6f7fb]">
        <div className="mx-auto max-w-4xl px-4 py-12 sm:px-8">
          <section className="space-y-10">
            <header className="space-y-2 text-left">
              <h1 className="text-3xl font-semibold text-slate-900 sm:text-4xl">
                원하는 근무 조건을 알려주세요.
              </h1>
              <p className="text-sm text-slate-500 sm:text-base">
                꼭 입력하지 않아도 되지만, 입력하시면 더 잘 맞는 공고를 찾아드려요.
              </p>
            </header>

            {error && (
              <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-600">
                {error}
              </div>
            )}

            <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
              <div className="grid gap-6 md:grid-cols-2">
                <div className="space-y-2">
                  <label
                    htmlFor="location"
                    className="text-sm font-medium text-slate-700"
                  >
                    위치
                  </label>
                  <input
                    id="location"
                    type="text"
                    value={locationInput}
                    onChange={(event) => setLocationInput(event.target.value)}
                    placeholder="ex. 서울특별시 강남구"
                    className="h-14 w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-base text-slate-700 placeholder-slate-400 focus:border-[rgb(96,150,222)] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[rgba(96,150,222,0.2)]"
                  />
                </div>
                <div className="space-y-2">
                  <label
                    htmlFor="employment"
                    className="text-sm font-medium text-slate-700"
                  >
                    고용 형태
                  </label>
                  <select
                    id="employment"
                    value={employmentType}
                    onChange={(event) => setEmploymentType(event.target.value)}
                    className="h-14 w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-base text-slate-700 focus:border-[rgb(96,150,222)] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[rgba(96,150,222,0.2)]"
                  >
                    {EMPLOYMENT_OPTIONS.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-2 md:col-span-2">
                  <span className="text-sm font-medium text-slate-700">
                    리모트 근무 선호
                  </span>
                  <div className="flex items-center gap-6">
                    <label className="flex items-center gap-2 text-sm text-slate-700">
                      <input
                        type="radio"
                        name="remote"
                        value="yes"
                        checked={remotePreference === "yes"}
                        onChange={() => setRemotePreference("yes")}
                        className="h-4 w-4 border border-slate-300 text-[rgb(96,150,222)] focus:ring-2 focus:ring-[rgba(96,150,222,0.3)]"
                      />
                      예
                    </label>
                    <label className="flex items-center gap-2 text-sm text-slate-700">
                      <input
                        type="radio"
                        name="remote"
                        value="no"
                        checked={remotePreference === "no"}
                        onChange={() => setRemotePreference("no")}
                        className="h-4 w-4 border border-slate-300 text-[rgb(96,150,222)] focus:ring-2 focus:ring-[rgba(96,150,222,0.3)]"
                      />
                      아니오
                    </label>
                  </div>
                </div>

                <div className="space-y-4 md:col-span-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-slate-700">
                      희망 연봉
                    </span>
                    <span className="text-sm font-semibold text-slate-800">
                      {formatNumber(salary)}원
                    </span>
                  </div>
                  <input
                    type="range"
                    min={SALARY_MIN}
                    max={SALARY_MAX}
                    step={SALARY_STEP}
                    value={salary}
                    onChange={(event) => setSalary(Number(event.target.value))}
                    className="w-full accent-[rgb(96,150,222)]"
                  />
                  <div className="flex justify-between text-xs text-slate-400">
                    <span>0원</span>
                    <span>2억+</span>
                  </div>
                </div>

                <div className="space-y-2">
                  <label
                    htmlFor="position"
                    className="text-sm font-medium text-slate-700"
                  >
                    직무
                  </label>
                  <input
                    id="position"
                    type="text"
                    value={position}
                    onChange={(event) => setPosition(event.target.value)}
                    placeholder="ex. Software Engineer"
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-base text-slate-700 placeholder-slate-400 focus:border-[rgb(96,150,222)] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[rgba(96,150,222,0.2)]"
                  />
                </div>
                <div className="space-y-2">
                  <label
                    htmlFor="industry"
                    className="text-sm font-medium text-slate-700"
                  >
                    산업
                  </label>
                  <input
                    id="industry"
                    type="text"
                    value={industry}
                    onChange={(event) => setIndustry(event.target.value)}
                    placeholder="ex. IT"
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-base text-slate-700 placeholder-slate-400 focus:border-[rgb(96,150,222)] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[rgba(96,150,222,0.2)]"
                  />
                </div>
              </div>

              <div className="mt-10 flex flex-col justify-end gap-3 sm:flex-row">
                <button
                  type="button"
                  onClick={handleSkip}
                  className="inline-flex items-center justify-center rounded-xl border border-[rgba(96,150,222,0.4)] bg-transparent px-6 py-3 text-sm font-semibold text-[rgb(96,150,222)] transition hover:border-[rgba(96,150,222,0.55)] hover:bg-[rgba(96,150,222,0.12)]"
                >
                  나중에 할게요
                </button>
                <button
                  type="button"
                  onClick={handleSavePreferences}
                  className="inline-flex items-center justify-center rounded-xl bg-[rgb(96,150,222)] px-6 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-[rgb(86,140,212)]"
                >
                  저장
                </button>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
