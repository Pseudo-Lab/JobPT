import React, { useState } from "react"; 


interface UploadViewProps {
  file: File | null;
  status: string;
  isDragging: boolean;
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  handleFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  handleAnalyze: () => void;
  handleDrop: (e: React.DragEvent<HTMLDivElement>) => void;
  setIsDragging: (dragging: boolean) => void;
  location: string;
  remote: string;
  jobType: string;
  setLocation: (val: string) => void;
  setRemote: (val: string) => void;
  setJobType: (val: string) => void;
}

import Link from 'next/link';

const UploadView: React.FC<UploadViewProps> = ({
  file,
  status,
  isDragging,
  fileInputRef,
  handleFileChange,
  handleAnalyze,
  handleDrop,
  setIsDragging,
  location,
  remote,
  jobType,
  setLocation,
  setRemote,
  setJobType
}) => {
  const [noPreference, setNoPreference] = useState(location === "");
  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] space-y-8">
      <h1 className="text-4xl font-bold text-indigo-700">📄 JobPT</h1>
      <p className="text-xl text-gray-600">이력서를 업로드하여 적합한 채용 정보를 찾아보세요</p>

      <div className="w-full max-w-lg space-y-4">
        <div
          onClick={() => fileInputRef.current?.click()}
          onDrop={handleDrop}
          onDragOver={e => e.preventDefault()}
          onDragEnter={() => setIsDragging(true)}
          onDragLeave={() => setIsDragging(false)}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors duration-300
            ${isDragging ? "border-indigo-500 bg-indigo-50" : "border-gray-300 bg-gray-50"}
            ${file ? "border-green-500" : ""}`}
        >
          {file ? (
            <div className="space-y-2">
              <div className="flex items-center justify-center">
                <svg className="w-12 h-12 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <p className="text-lg font-medium text-green-600">파일이 준비되었습니다</p>
              <p className="text-gray-700">{file.name}</p>
            </div>
          ) : (
            <>
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <p className="text-indigo-600 font-semibold mt-2">이력서 파일을 여기에 끌어다 놓거나 클릭하여 선택</p>
              <p className="text-sm text-gray-500 mt-1">지원 형식: PDF, PNG, JPG, JPEG, GIF</p>
            </>
          )}
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.png,.jpg,.jpeg,.gif"
          onChange={handleFileChange}
          className="hidden"
        />

        {/* 🔽 필터 입력 */}
        <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">📍 선호 지역</label>
          <div className="mt-1 flex items-center gap-2">
            <input
              type="text"
              value={noPreference ? "" : location}
              onChange={(e) => {
                setLocation(e.target.value);
                if (noPreference && e.target.value !== "") setNoPreference(false);
              }}
              placeholder="예: 서울"
              className="flex-1 rounded-md border-gray-300 shadow-sm"
              disabled={noPreference}
            />
            <label className="flex items-center space-x-1 text-sm text-gray-600">
              <input
                type="checkbox"
                checked={noPreference}
                onChange={(e) => {
                  setNoPreference(e.target.checked);
                  if (e.target.checked) {
                    setLocation(""); // 상관없음이면 location 비움
                  }
                }}
              />
              <span>상관없음</span>
            </label>
          </div>
        </div>



          <div>
            <label className="block text-sm font-medium text-gray-700">💻 원격 근무</label>
            <select
              value={remote}
              onChange={(e) => setRemote(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
            >
              <option value="any">상관없음</option>
              <option value="yes">희망</option>
              <option value="no">비희망</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">🕒 고용 형태</label>
            <select
              value={jobType}
              onChange={(e) => setJobType(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
            >
              <option value="any">상관없음</option>
              <option value="full-time">풀타임</option>
              <option value="part-time">파트타임</option>
            </select>
          </div>
        </div>
      </div>

      {file && (
        <div className="flex flex-wrap justify-center gap-4">
          <button
            onClick={handleAnalyze}
            className="px-6 py-3 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 font-medium text-lg shadow-md transition duration-300 transform hover:scale-105"
          >
            🔍 분석하기
          </button>
          <button
            onClick={handleAnalyze}
            className="px-6 py-3 rounded-lg bg-yellow-500 text-white hover:bg-yellow-600 font-medium text-lg shadow-md transition duration-300 transform hover:scale-105"
          >
            ✏️ 수정하기
          </button>
          <Link href="/evaluate">
  <button
    className="px-6 py-3 rounded-lg bg-green-600 text-white hover:bg-green-700 font-medium text-lg shadow-md transition duration-300 transform hover:scale-105"
  >
    📝 평가받기
  </button>
</Link>
        </div>
      )}

      <p className={`mt-2 ${status === "Processing..." ? "text-amber-600 animate-pulse" : status === "Complete!" ? "text-green-600" : status.includes("Error") ? "text-red-600" : "text-gray-500"}`}>
        {status}
      </p>
    </div>
  );
};

export default UploadView;
