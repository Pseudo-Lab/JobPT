import React from "react";

export interface ResumeExperience {
  company: string;
  period: string;
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
}: {
  summary: ResumeSummaryData;
  className?: string;
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
        <div>
          <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">{name}</h1>
          <div className="mt-2 flex flex-wrap gap-4 text-sm text-slate-600">
            {phone && (
              <span className="inline-flex items-center gap-2">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                  className="h-4 w-4 text-slate-400"
                >
                  <path d="M6.62 10.79a15.91 15.91 0 006.59 6.59l2.2-2.2a1 1 0 011.02-.24 12.66 12.66 0 004 0.64 1 1 0 011 1v3.5a1 1 0 01-.89 1 18.91 18.91 0 01-8.21-2.45 18.7 18.7 0 01-6-6 18.91 18.91 0 01-2.45-8.21A1 1 0 015 3h3.5a1 1 0 011 1 12.66 12.66 0 00.64 4 1 1 0 01-.25 1.02z" />
                </svg>
                {phone}
              </span>
            )}
            {email && (
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
                {email}
              </span>
            )}
          </div>
        </div>

        {intro && (
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
            {intro}
          </p>
        )}
      </header>

      {experiences.length > 0 && (
        <section className="space-y-4">
          <SectionTitle>경력</SectionTitle>
          <div className="space-y-8">
            {experiences.map((exp, idx) => (
              <div key={`${exp.company}-${idx}`} className="space-y-3">
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
                  <div className="space-y-1">
                    <p className="text-base font-semibold text-slate-900">
                      {exp.company}
                    </p>
                    <p className="text-sm text-slate-500">{exp.period}</p>
                  </div>
                </div>

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
              </div>
            ))}
          </div>
        </section>
      )}

      {skills.length > 0 && (
        <section className="space-y-4">
          <SectionTitle>스킬</SectionTitle>
          <div className="flex flex-wrap gap-2">
            {skills.map((skill) => (
              <span
                key={skill}
                className="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700"
              >
                {skill}
              </span>
            ))}
          </div>
        </section>
      )}

      {certifications.length > 0 && (
        <section className="space-y-4">
          <SectionTitle>수상/자격증/기타</SectionTitle>
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
        </section>
      )}

      {languages.length > 0 && (
        <section className="space-y-4">
          <SectionTitle>언어</SectionTitle>
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
        </section>
      )}

      {links.length > 0 && (
        <section className="space-y-4">
          <SectionTitle>링크</SectionTitle>
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
        </section>
      )}
    </div>
  );
};

export default ResumeSummaryView;
