import React, { memo } from "react";
import { UploadViewProps } from "@/types/upload";

import Link from 'next/link';
import Image from 'next/image';

const UploadView: React.FC<UploadViewProps> = memo(({
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
  setJobType,
  handleManualJD
}) => {
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
          <div className="mt-1 flex gap-4">
            <label className={`flex items-center gap-2 px-2 py-1 rounded cursor-pointer transition-colors ${location[0]==='USA' ? 'bg-indigo-100 text-indigo-700 font-semibold' : 'text-gray-700'}`}>
  <input
    type="radio"
    name="location-category"
    value="USA"
    checked={location[0] === 'USA'}
    onChange={() => setLocation(['USA'])}
    className="accent-indigo-500"
  />
  USA
</label>
<label className={`flex items-center gap-2 px-2 py-1 rounded cursor-pointer transition-colors ${location[0]==='Germany' ? 'bg-indigo-100 text-indigo-700 font-semibold' : 'text-gray-700'}`}>
  <input
    type="radio"
    name="location-category"
    value="Germany"
    checked={location[0] === 'Germany'}
    onChange={() => setLocation(['Germany'])}
    className="accent-indigo-500"
  />
  Germany
</label>
<label className={`flex items-center gap-2 px-2 py-1 rounded cursor-pointer transition-colors ${location[0]==='UK' ? 'bg-indigo-100 text-indigo-700 font-semibold' : 'text-gray-700'}`}>
  <input
    type="radio"
    name="location-category"
    value="UK"
    checked={location[0] === 'UK'}
    onChange={() => setLocation(['UK'])}
    className="accent-indigo-500"
  />
  UK
</label>
          </div>
        </div>



          <div>
            <label className="block text-sm font-medium text-gray-700">💻 원격 근무</label>
            <div className="flex gap-4 mt-1">
              <label className={`flex items-center gap-2 px-2 py-1 rounded cursor-pointer transition-colors ${remote.includes(true) ? 'bg-green-100 text-green-700 font-semibold' : 'text-gray-700'}`}>
  <input
    type="checkbox"
    checked={remote.includes(true)}
    onChange={e => {
      if (e.target.checked) setRemote(Array.from(new Set([...remote, true])));
      else setRemote(remote.filter(r => r !== true));
    }}
    className="accent-green-500"
  />
  희망
</label>
<label className={`flex items-center gap-2 px-2 py-1 rounded cursor-pointer transition-colors ${remote.includes(false) ? 'bg-red-100 text-red-700 font-semibold' : 'text-gray-700'}`}>
  <input
    type="checkbox"
    checked={remote.includes(false)}
    onChange={e => {
      if (e.target.checked) setRemote(Array.from(new Set([...remote, false])));
      else setRemote(remote.filter(r => r !== false));
    }}
    className="accent-red-500"
  />
  비희망
</label>
            </div>
            <span className="text-xs text-gray-400">복수선택 가능</span>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">🕒 고용 형태</label>
            <div className="flex gap-4 mt-1">
              <label className={`flex items-center gap-2 px-2 py-1 rounded cursor-pointer transition-colors ${jobType.includes('fulltime') ? 'bg-blue-100 text-blue-700 font-semibold' : 'text-gray-700'}`}>
  <input
    type="checkbox"
    checked={jobType.includes('fulltime')}
    onChange={e => {
      if (e.target.checked) setJobType(Array.from(new Set([...jobType, 'fulltime'])));
      else setJobType(jobType.filter(j => j !== 'fulltime'));
    }}
    className="accent-blue-500"
  />
  풀타임
</label>
<label className={`flex items-center gap-2 px-2 py-1 rounded cursor-pointer transition-colors ${jobType.includes('parttime') ? 'bg-yellow-100 text-yellow-700 font-semibold' : 'text-gray-700'}`}>
  <input
    type="checkbox"
    checked={jobType.includes('parttime')}
    onChange={e => {
      if (e.target.checked) setJobType(Array.from(new Set([...jobType, 'parttime'])));
      else setJobType(jobType.filter(j => j !== 'parttime'));
    }}
    className="accent-yellow-500"
  />
  파트타임
</label>
            </div>
            <span className="text-xs text-gray-400">복수선택 가능</span>
          </div>
        </div>
      </div>

      {file && (
        <div className="flex flex-wrap justify-center gap-4">
          <button
            className="px-6 py-3 rounded-lg bg-blue-600 text-white hover:bg-blue-700 font-medium text-lg shadow-md transition duration-300 transform hover:scale-105 flex items-center justify-center min-w-[120px]"
            onClick={handleAnalyze}
            disabled={status === "Processing..."}
          >
            {status === "Processing..." ? (
              <Image 
                src="/logo/loading.gif" 
                alt="loading" 
                width={28} 
                height={28} 
                style={{ background: '#fff', borderRadius: 8 }} 
              />
            ) : (
              <><span role="img" aria-label="분석">🔍</span> 분석하기</>
            )}
          </button>
          <button
            onClick={handleManualJD}
            className="px-6 py-3 rounded-lg bg-yellow-500 text-white hover:bg-yellow-600 font-medium text-lg shadow-md transition duration-300 transform hover:scale-105 flex items-center justify-center min-w-[120px]"
            disabled={status === "Processing..."}
          >
            {status === "Processing..." ? (
              <Image 
                src="/logo/loading.gif" 
                alt="loading" 
                width={28} 
                height={28} 
                style={{ background: '#fff', borderRadius: 8 }} 
              />
            ) : (
              <><span role="img" aria-label="업로드">📤</span> JD/CV 업로드하기</>
            )}
          </button>
          <Link href="/evaluate">
            <button
              className="px-6 py-3 rounded-lg bg-green-600 text-white hover:bg-green-700 font-medium text-lg shadow-md transition duration-300 transform hover:scale-105 flex items-center justify-center min-w-[120px]"
              disabled={status === "Processing..."}
            >
              {status === "Processing..." ? (
                <Image 
                  src="/logo/loading.gif" 
                  alt="loading" 
                  width={28} 
                  height={28} 
                  style={{ background: '#fff', borderRadius: 8 }} 
                />
              ) : (
                <><span role="img" aria-label="평가">📝</span> 평가받기</>
              )}
            </button>
          </Link>
        </div>
      )}

      <p className={`mt-2 ${status === "Processing..." ? "text-amber-600 animate-pulse" : status === "Complete!" ? "text-green-600" : status.includes("Error") ? "text-red-600" : "text-gray-500"}`}>
        {status}
      </p>
    </div>
  );
});

UploadView.displayName = 'UploadView';

export default UploadView;
