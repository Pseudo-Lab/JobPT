import React, { useEffect, useState } from "react";

export interface ResumeExperience {
  company: string;
  period: string;
  startDate?: string;
  endDate?: string;
  title?: string;
  description?: string;
  logoUrl?: string;
}

export interface ResumeCertification {
  name: string;
  date?: string;
  note?: string;
}

export interface ResumeLanguage {
  name: string;
  details?: string[];
}

export interface ResumeLink {
  label: string;
  url: string;
}

export interface ResumeSummaryData {
  name: string;
  phone?: string;
  email?: string;
  summary?: string;
  experiences?: ResumeExperience[];
  skills?: string[];
  certifications?: ResumeCertification[];
  languages?: ResumeLanguage[];
  links?: ResumeLink[];
}

const SectionTitle = ({ children }: { children: React.ReactNode }) => (
  <div className="border-b border-slate-200 pb-3 text-base font-semibold text-slate-900">
    {children}
  </div>
);

const ResumeSummaryView = ({
  summary,
  className,
  editable = false,
  // onAttach,
  onChange,
}: {
  summary: ResumeSummaryData;
  className?: string;
  editable?: boolean;
  // onAttach?: (attachment: { id: string; label: string; content: string }) => void;
  onChange?: (next: ResumeSummaryData) => void;
}) => {
  const {
    name,
    phone,
    email,
    summary: intro,
    experiences = [],
    skills = [],
    certifications = [],
    languages = [],
    links = [],
  } = summary;

  const [introValue, setIntroValue] = useState(intro ?? "");
  const [experienceValues, setExperienceValues] = useState<ResumeExperience[]>(experiences);
  const [skillsValues, setSkillsValues] = useState<string[]>(skills);
  const [skillInput, setSkillInput] = useState("");
  const [certInput, setCertInput] = useState(
    (certifications ?? [])
      .map((cert) => [cert.name, cert.date, cert.note].filter(Boolean).join(" / "))
      .join("\n"),
  );
  const [languageInput, setLanguageInput] = useState(
    (languages ?? [])
      .map((lang) => [lang.name, ...(lang.details || [])].join(" - "))
      .join("\n"),
  );
  const [linkInput, setLinkInput] = useState(
    (links ?? [])
      .map((link) => `${link.label}${link.url ? ` - ${link.url}` : ""}`)
      .join("\n"),
  );

  const parseLines = (value: string) =>
    value
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean);

  const parseCertifications = (value: string): ResumeCertification[] =>
    parseLines(value).map((line) => {
      const parts = line.split("/").map((p) => p.trim()).filter(Boolean);
      const [name, date, note] = parts;
      return { name: name || line, date, note };
    });

  const parseLanguages = (value: string): ResumeLanguage[] =>
    parseLines(value).map((line) => {
      const parts = line.split("-").map((p) => p.trim()).filter(Boolean);
      const [name, ...rest] = parts;
      const details = rest.join(" - ").trim();
      if (details) {
        return {
          name: name || line,
          details: [details],
        };
      }
      return {
        name: name || line,
      };
    });

  const parseLinks = (value: string): ResumeLink[] =>
    parseLines(value).map((line) => {
      const [label, ...rest] = line.split("-").map((p) => p.trim());
      const url = rest.join("-").trim();
      return {
        label: label || line,
        url: url || "",
      };
    });

  useEffect(() => {
    if (!editable) {
      setIntroValue(intro ?? "");
    }
  }, [editable, intro]);

  useEffect(() => {
    if (!editable) {
      setExperienceValues(experiences);
      setSkillsValues(skills);
      setCertInput(
        (certifications ?? [])
          .map((cert) => [cert.name, cert.date, cert.note].filter(Boolean).join(" / "))
          .join("\n"),
      );
      setLanguageInput(
        (languages ?? [])
          .map((lang) => [lang.name, ...(lang.details || [])].join(" - "))
          .join("\n"),
      );
      setLinkInput(
        (links ?? [])
          .map((link) => `${link.label}${link.url ? ` - ${link.url}` : ""}`)
          .join("\n"),
      );
    }
  }, [certifications, editable, experiences, languages, links, skills]);

  useEffect(() => {
    if (editable && experienceValues.length === 0) {
      setExperienceValues([
        {
          company: "",
          period: "",
          startDate: "",
          endDate: "",
          title: "",
          description: "",
          logoUrl: "",
        },
      ]);
    }
  }, [editable, experienceValues.length]);

  const experiencesToRender =
    editable && experienceValues.length === 0
      ? [
          {
            company: "",
            period: "",
            startDate: "",
            endDate: "",
            title: "",
            description: "",
            logoUrl: "",
          },
        ]
      : editable
        ? experienceValues
        : experiences;

  const addSkill = () => {
    const trimmed = skillInput.trim();
    if (!trimmed) return;
    if (skillsValues.includes(trimmed)) {
      setSkillInput("");
      return;
    }
    setSkillsValues((prev) => [...prev, trimmed]);
    setSkillInput("");
  };

  const removeSkill = (value: string) => {
    setSkillsValues((prev) => prev.filter((item) => item !== value));
  };

  // const addExperience = () => {
  //   setExperienceValues((prev) => [
  //     ...prev,
  //     {
  //       company: "",
  //       period: "",
  //       startDate: "",
  //       endDate: "",
  //       title: "",
  //       description: "",
  //       logoUrl: "",
  //     },
  //   ]);
  // };

  useEffect(() => {
    if (!onChange) return;
    onChange({
      ...summary,
      summary: introValue,
      experiences: experienceValues,
      skills: skillsValues,
      certifications: parseCertifications(certInput),
      languages: parseLanguages(languageInput),
      links: parseLinks(linkInput),
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [certInput, experienceValues, introValue, languageInput, linkInput, skillsValues]);

  const renderInput = (props: React.InputHTMLAttributes<HTMLInputElement>) => (
    <input
      {...props}
      className={[
        "w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-800",
        "focus:border-[rgb(96,150,222)] focus:outline-none focus:ring-2 focus:ring-[rgba(96,150,222,0.2)]",
        props.className,
      ]
        .filter(Boolean)
        .join(" ")}
    />
  );

  const renderTextArea = (
    props: React.TextareaHTMLAttributes<HTMLTextAreaElement>,
  ) => (
    <textarea
      {...props}
      className={[
        "w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-800",
        "focus:border-[rgb(96,150,222)] focus:outline-none focus:ring-2 focus:ring-[rgba(96,150,222,0.2)]",
        props.className,
      ]
        .filter(Boolean)
        .join(" ")}
    />
  );

  const formatPeriod = (exp: ResumeExperience) => {
    if (exp.period && exp.period.trim().length > 0) return exp.period;
    const start = exp.startDate && exp.startDate.trim().length > 0 ? exp.startDate : null;
    const end = exp.endDate && exp.endDate.trim().length > 0 ? exp.endDate : null;
    if (start || end) {
      return `${start ?? "시작일"} ~ ${end ?? "종료일"}`;
    }
    return "";
  };

  // const attachSummary = () => {
  //   if (!onAttach) return;
  //   const content =
  //     introValue && introValue.trim().length > 0
  //       ? introValue
  //       : "자기소개 내용이 아직 없습니다.";
  //   onAttach({
  //     id: "summary",
  //     label: "자기소개",
  //     content,
  //   });
  // };

  // const attachExperience = () => {
  //   if (!onAttach || experienceValues.length === 0) return;
  //   const combined = experienceValues
  //     .map((exp, idx) => {
  //       const lines = [
  //         exp.company ? `회사명: ${exp.company}` : null,
  //         formatPeriod(exp) ? `기간: ${formatPeriod(exp)}` : null,
  //         exp.title ? `역할: ${exp.title}` : null,
  //         exp.description ? `내용: ${exp.description}` : null,
  //       ]
  //         .filter(Boolean)
  //         .join(" | ");
  //       return lines ? `경력 ${idx + 1}: ${lines}` : null;
  //     })
  //     .filter(Boolean)
  //     .join("\n\n");

  //   const content =
  //     combined && combined.trim().length > 0
  //       ? combined
  //       : "경력 내용이 아직 없습니다.";
  //   onAttach({
  //     id: "experience",
  //     label: "경력",
  //     content,
  //   });
  // };

  // const AttachButton = ({
  //   onClick,
  //   label,
  // }: {
  //   onClick: () => void;
  //   label: string;
  // }) => (
  //   <button
  //     type="button"
  //     onClick={onClick}
  //     className="inline-flex h-10 w-10 items-center justify-center rounded-[12px] bg-[#d9e9ff] text-[rgb(77,136,205)] shadow-sm transition hover:-translate-y-0.5 hover:shadow"
  //     aria-label={label}
  //   >
  //     <svg
  //       xmlns="http://www.w3.org/2000/svg"
  //       viewBox="0 0 24 24"
  //       fill="none"
  //       stroke="currentColor"
  //       strokeWidth={1.8}
  //       className="h-5 w-5"
  //     >
  //       <path
  //         strokeLinecap="round"
  //         strokeLinejoin="round"
  //         d="M5.25 5.25L18.75 12 5.25 18.75 9 12z"
  //       />
  //     </svg>
  //   </button>
  // );

  return (
    <div
      className={[
        "flex h-full flex-col gap-8 rounded-3xl border border-slate-200 bg-white p-8 shadow-sm",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <header className="space-y-4">
        <div className="space-y-3">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">
                {name || "홍길동"}
              </h1>
              <div className="mt-2 flex flex-wrap gap-4 text-sm text-slate-600">
                <span className="inline-flex items-center gap-2">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="currentColor"
                    className="h-4 w-4 text-slate-400"
                  >
                    <path d="M6.62 10.79a15.91 15.91 0 006.59 6.59l2.2-2.2a1 1 0 011.02-.24 12.66 12.66 0 004 0.64 1 1 0 011 1v3.5a1 1 0 01-.89 1 18.91 18.91 0 01-8.21-2.45 18.7 18.7 0 01-6-6 18.91 18.91 0 01-2.45-8.21A1 1 0 015 3h3.5a1 1 0 011 1 12.66 12.66 0 00.64 4 1 1 0 01-.25 1.02z" />
                  </svg>
                  {phone || "010-0000-0000"}
                </span>
                <span className="inline-flex items-center gap-2">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth={1.5}
                    className="h-4 w-4 text-slate-400"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M3.75 6.75A2.25 2.25 0 016 4.5h12a2.25 2.25 0 012.25 2.25v10.5A2.25 2.25 0 0118 19.5H6a2.25 2.25 0 01-2.25-2.25V6.75z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M4.5 7.5l6.75 4.219a.75.75 0 00.78 0L18.75 7.5"
                    />
                  </svg>
                  {email || "email@gmail.com"}
                </span>
              </div>
            </div>
            {/* {editable && onAttach && (
              <AttachButton onClick={attachSummary} label="자기소개 첨부" />
            )} */}
          </div>
        </div>

        {editable ? (
          renderTextArea({
            rows: 4,
            placeholder: "자기소개를 입력하세요.",
            value: introValue,
            onChange: (e) => setIntroValue(e.target.value),
            "aria-label": "자기소개",
          })
        ) : (
          intro && (
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
              {intro}
            </p>
          )
        )}
      </header>

      {(editable || experiencesToRender.length > 0) && (
        <section className="space-y-4">
          <div className="flex items-center justify-between border-b border-slate-200 pb-3">
            <span className="text-base font-semibold text-slate-900">경력</span>
            {editable && (
              <div className="flex items-center gap-2">
                {/* <button
                  type="button"
                  onClick={addExperience}
                  className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-500 shadow-sm transition hover:-translate-y-0.5 hover:text-[rgb(96,150,222)]"
                  aria-label="경력 추가"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth={1.7}
                    className="h-5 w-5"
                  >
                    <path d="M12 6v12M6 12h12" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </button> */}
                {/* {onAttach && <AttachButton onClick={attachExperience} label="경력 첨부" />} */}
              </div>
            )}
          </div>
          <div className="space-y-8">
            {experiencesToRender.map((exp, idx) => (
              <div key={`experience-${idx}`} className="space-y-3">
                <div className="flex items-start gap-4">
                  <div className="flex h-12 w-12 items-center justify-center overflow-hidden rounded-full border border-slate-200 bg-slate-50">
                    {exp.logoUrl ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={exp.logoUrl}
                        alt={`${exp.company} logo`}
                        className="h-full w-full object-contain p-2"
                      />
                    ) : (
                      <div className="text-xs font-semibold text-slate-400">
                        logo
                      </div>
                    )}
                  </div>
                  <div className="space-y-1 flex-1">
                    {editable ? (
                      <div className="space-y-2">
                        {renderInput({
                          placeholder: "회사명",
                          value: exp.company ?? "",
                          onChange: (e) =>
                            setExperienceValues((prev) => {
                              const next = [...prev];
                              const base =
                                next[idx] ??
                                { company: "", period: "", startDate: "", endDate: "", title: "", description: "", logoUrl: "" };
                              next[idx] = { ...base, company: e.target.value };
                              return next;
                            }),
                          "aria-label": `경력 ${idx + 1} 회사명`,
                        })}
                        <div className="grid gap-2 sm:grid-cols-2">
                          {renderInput({
                            type: "date",
                            value: exp.startDate ?? "",
                            onChange: (e) =>
                              setExperienceValues((prev) => {
                                const next = [...prev];
                                const base =
                                  next[idx] ??
                                  { company: "", period: "", startDate: "", endDate: "", title: "", description: "", logoUrl: "" };
                                next[idx] = { ...base, startDate: e.target.value, period: "" };
                                return next;
                              }),
                            "aria-label": `경력 ${idx + 1} 시작일`,
                          })}
                          {renderInput({
                            type: "date",
                            value: exp.endDate ?? "",
                            onChange: (e) =>
                              setExperienceValues((prev) => {
                                const next = [...prev];
                                const base =
                                  next[idx] ??
                                  { company: "", period: "", startDate: "", endDate: "", title: "", description: "", logoUrl: "" };
                                next[idx] = { ...base, endDate: e.target.value, period: "" };
                                return next;
                              }),
                            "aria-label": `경력 ${idx + 1} 종료일`,
                          })}
                        </div>
                      </div>
                    ) : (
                      <>
                        <p className="text-base font-semibold text-slate-900">
                          {exp.company}
                        </p>
                        <p className="text-sm text-slate-500">{formatPeriod(exp)}</p>
                      </>
                    )}
                  </div>
                </div>

                {editable ? (
                  <>
                    {renderInput({
                      placeholder: "역할/타이틀",
                      value: exp.title ?? "",
                      onChange: (e) =>
                        setExperienceValues((prev) => {
                          const next = [...prev];
                          next[idx] = { ...next[idx], title: e.target.value };
                          return next;
                        }),
                      "aria-label": `경력 ${idx + 1} 타이틀`,
                    })}
                    {renderTextArea({
                      rows: 4,
                      placeholder: "주요 업무 및 성과를 작성하세요.",
                      value: exp.description ?? "",
                      onChange: (e) =>
                        setExperienceValues((prev) => {
                          const next = [...prev];
                          next[idx] = { ...next[idx], description: e.target.value };
                          return next;
                        }),
                      "aria-label": `경력 ${idx + 1} 설명`,
                    })}
                  </>
                ) : (
                  <>
                    {exp.title && (
                      <p className="text-sm font-semibold text-slate-800">
                        {exp.title}
                      </p>
                    )}
                    {exp.description && (
                      <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
                        {exp.description}
                      </p>
                    )}
                  </>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {(editable || skills.length > 0) && (
        <section className="space-y-4">
          <SectionTitle>스킬</SectionTitle>
          {editable ? (
            <div className="space-y-3">
              <div className="flex flex-wrap gap-2">
                {skillsValues.map((skill) => (
                  <span
                    key={skill}
                    className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm"
                  >
                    {skill}
                    <button
                      type="button"
                      onClick={() => removeSkill(skill)}
                      className="text-slate-400 transition hover:text-slate-600"
                      aria-label={`${skill} 삭제`}
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={skillInput}
                  onChange={(e) => setSkillInput(e.target.value)}
                  onKeyDown={(e) => {
                    // Avoid committing while IME composition is in progress
                    if ((e as React.KeyboardEvent<HTMLInputElement>).nativeEvent.isComposing) {
                      return;
                    }
                    if (e.key === "Enter") {
                      e.preventDefault();
                      addSkill();
                    }
                  }}
                  placeholder="스킬을 입력 후 Enter 또는 추가"
                  className="flex-1 rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-[rgb(96,150,222)] focus:outline-none focus:ring-2 focus:ring-[rgba(96,150,222,0.2)]"
                  aria-label="스킬 추가 입력"
                />
                <button
                  type="button"
                  onClick={addSkill}
                  className="rounded-xl bg-[rgb(96,150,222)] px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-[rgb(86,140,212)]"
                >
                  추가
                </button>
              </div>
            </div>
          ) : (
            <div className="flex flex-wrap gap-2">
              {skillsValues.map((skill) => (
                <span
                  key={skill}
                  className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm"
                >
                  {skill}
                </span>
              ))}
            </div>
          )}
        </section>
      )}

      {(editable || certifications.length > 0) && (
        <section className="space-y-4">
          <SectionTitle>수상/자격증/기타</SectionTitle>
          {editable ? (
            renderTextArea({
              rows: 3,
              placeholder: "수상/자격증을 줄바꿈으로 구분해 입력하세요.",
              value: certInput,
              onChange: (e) => setCertInput(e.target.value),
              "aria-label": "수상/자격증",
            })
          ) : (
            <div className="space-y-4">
              {certifications.map((cert, idx) => (
                <div key={`${cert.name}-${idx}`} className="flex items-start gap-3">
                  <span className="mt-1 inline-flex h-6 w-6 items-center justify-center rounded-full border border-slate-200 text-slate-400">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth={1.5}
                      className="h-3.5 w-3.5"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M12 6v12m-6-6h12"
                      />
                    </svg>
                  </span>
                  <div className="space-y-1">
                    <p className="text-sm font-semibold text-slate-900">{cert.name}</p>
                    {cert.date && <p className="text-xs text-slate-500">{cert.date}</p>}
                    {cert.note && (
                      <p className="text-xs text-slate-600">{cert.note}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {(editable || languages.length > 0) && (
        <section className="space-y-4">
          <SectionTitle>언어</SectionTitle>
          {editable ? (
            renderTextArea({
              rows: 3,
              placeholder: "언어와 레벨을 줄바꿈으로 입력하세요. (예: 영어 - TOEIC 900)",
              value: languageInput,
              onChange: (e) => setLanguageInput(e.target.value),
              "aria-label": "언어",
            })
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {languages.map((lang) => (
                <div
                  key={lang.name}
                  className="space-y-1 rounded-2xl border border-slate-200 px-4 py-3"
                >
                  <p className="text-sm font-semibold text-slate-900">{lang.name}</p>
                  {lang.details?.map((detail, idx) => (
                    <p key={`${lang.name}-${idx}`} className="text-xs text-slate-600">
                      {detail}
                    </p>
                  ))}
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {(editable || links.length > 0) && (
        <section className="space-y-4">
          <SectionTitle>링크</SectionTitle>
          {editable ? (
            renderTextArea({
              rows: 3,
              placeholder: "링크를 줄바꿈으로 입력하세요. (예: 포트폴리오 - https://...)",
              value: linkInput,
              onChange: (e) => setLinkInput(e.target.value),
              "aria-label": "링크",
            })
          ) : (
            <ul className="space-y-2">
              {links.map((link) => (
                <li key={link.url}>
                  <a
                    href={link.url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-2 text-sm text-slate-600 underline decoration-slate-300 underline-offset-4 transition hover:text-slate-900"
                  >
                    <span className="h-1 w-1 rounded-full bg-slate-400" />
                    <span>{link.label}</span>
                  </a>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </div>
  );
};

export default ResumeSummaryView;
