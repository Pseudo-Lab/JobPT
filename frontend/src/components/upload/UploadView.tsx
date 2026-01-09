import React, { memo } from "react";
import { UploadViewProps } from "@/types/upload";

const UploadView: React.FC<UploadViewProps> = memo(
  ({
    file,
    status,
    isDragging,
    fileInputRef,
    handleFileChange,
    handleAnalyze,
    handleDrop,
    setIsDragging,
    jobPostingUrl,
    onJobPostingUrlChange,
  }) => {
    const isProcessing = status === "Processing...";

    const uploadCardState = [
      "mt-6 flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-10 text-center transition-colors duration-300 cursor-pointer",
      isDragging ? "border-blue-400 bg-blue-50" : "border-slate-300 bg-slate-50",
      file ? "border-blue-500 bg-blue-50" : "",
    ].join(" ");

    return (
      <section className="flex flex-col gap-8">
        <header className="space-y-2">
          <h1 className="text-3xl font-semibold text-slate-900 md:text-4xl">
            JobPT 시작하기
          </h1>
          <p className="text-sm text-slate-500 md:text-base">
            이력서를 업로드하고, 맞춤 공고를 받아보세요 (멘트 수정)
          </p>
        </header>

        <div className="space-y-6">
          <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
            <div className="flex items-baseline justify-between">
              <h2 className="text-lg font-semibold text-slate-800">
                Upload Resume (Required)
              </h2>
            </div>

            <div
              role="button"
              tabIndex={0}
              onClick={() => fileInputRef.current?.click()}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  fileInputRef.current?.click();
                }
              }}
              onDrop={(event) => {
                handleDrop(event);
              }}
              onDragOver={(event) => event.preventDefault()}
              onDragEnter={() => setIsDragging(true)}
              onDragLeave={() => setIsDragging(false)}
              className={uploadCardState}
            >
              {file ? (
                <div className="space-y-3">
                  <svg
                    className="mx-auto h-14 w-14 text-blue-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.8}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  <div className="space-y-1">
                    <p className="text-base font-semibold text-slate-800">
                      {file.name}
                    </p>
                    <p className="text-sm text-slate-500">
                      다른 파일로 교체하려면 다시 업로드하세요.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-white shadow-sm">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      strokeWidth={1.5}
                      stroke="currentColor"
                      className="h-8 w-8 text-blue-500"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M3 6.75C3 5.784 3 5.302 3.152 4.911a2.25 2.25 0 011.337-1.337C4.88 3.422 5.363 3.422 6.328 3.422h11.344c.965 0 1.447 0 1.838.152a2.25 2.25 0 011.337 1.337c.152.391.152.874.152 1.839v10.5c0 .965 0 1.447-.152 1.838a2.25 2.25 0 01-1.337 1.337c-.391.152-.873.152-1.838.152H6.328c-.965 0-1.447 0-1.838-.152a2.25 2.25 0 01-1.337-1.337C3 18.697 3 18.215 3 17.25V6.75z"
                      />
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M8.25 7.5h7.5M8.25 11.25h7.5M11.25 15h4.5"
                      />
                    </svg>
                  </div>
                  <div className="space-y-1">
                    <p className="text-base font-medium text-blue-600">
                      Upload a file or drag and drop
                    </p>
                    <p className="text-sm text-slate-500">
                      PDF, DOCX, TXT, 이미지 (최대 10MB)
                    </p>
                  </div>
                </div>
              )}
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg,.gif"
              onChange={handleFileChange}
              className="hidden"
            />
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
            <label
              htmlFor="job-posting-url"
              className="text-lg font-semibold text-slate-800"
            >
              Job Posting URL
              <span className="ml-2 text-sm font-medium text-slate-400">
                (Optional)
              </span>
            </label>
            <input
              id="job-posting-url"
              type="url"
              value={jobPostingUrl}
              onChange={(event) => onJobPostingUrlChange(event.target.value)}
              placeholder="https://www.linkedin.com/jobs/view/..."
              className="mt-4 w-full rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-base text-slate-700 placeholder:underline shadow-inner transition focus:border-blue-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-100"
            />
            <p className="mt-3 text-sm text-slate-400">
              희망하는 공고가 있다면 해당 링크를 입력해주세요. 공고에 맞춰
              이력서 수정을 도와드릴게요.
            </p>
          </div>

          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <button
              type="button"
              onClick={handleAnalyze}
              disabled={!file || isProcessing}
              className={`ml-auto inline-flex items-center justify-center gap-2 rounded-full px-6 py-3 text-base font-semibold transition ${
                !file || isProcessing
                  ? "cursor-not-allowed bg-slate-300 text-slate-500"
                  : "bg-[rgb(96,150,222)] text-white shadow-md hover:bg-[rgb(86,140,212)]"
              }`}
            >
              다음 단계로
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
                  d="M13.5 4.5l6 7.5-6 7.5M4.5 12h15"
                />
              </svg>
            </button>
          </div>
        </div>
      </section>
    );
  },
);

UploadView.displayName = "UploadView";

export default UploadView;
