"use client";
import Link from 'next/link';
import DOMPurify from 'dompurify';
import { marked } from "marked";
import React from 'react';
import PdfHighlighterView from './PdfHighlighterView';

type SectionBox = {
  id: string;
  title: string;
  x: number;
  y: number;
  width: number;
  height: number;
  text: string;
};

import type { RawElement } from "./types";

type ResultViewProps = {
  pdfError: string | null;
  isPdf: boolean;
  sectionBoxes: SectionBox[];
  handleSectionClick: (box: SectionBox) => void;
  thumbnailUrl: string | null;
  company: string;
  JD: string;
  JD_url: string;
  output: string;
  handleBackToUpload: () => void;
  pdfUrl: string | null;
  rawElements: RawElement[];
  userResumeDraft: string;
  setUserResumeDraft: (val: string) => void;
  userResume: string;
  setUserResume: (val: string) => void;
};

const ResultView: React.FC<ResultViewProps> = ({
  pdfError,
  isPdf,
  sectionBoxes,
  handleSectionClick,
  thumbnailUrl,
  company,
  JD,
  JD_url,
  output,
  handleBackToUpload,
  pdfUrl,
  rawElements,
  userResumeDraft,
  setUserResumeDraft,
  userResume,
  setUserResume,
}) => {
  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-4">
        <button 
          onClick={handleBackToUpload}
          className="px-4 py-2 flex items-center text-indigo-600 hover:text-indigo-800"
        >
          <svg className="w-5 h-5 mr-1" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M7.707 14.707a1 1 0 01-1.414 0l-5-5a1 1 0 010-1.414l5-5a1 1 0 111.414 1.414L4.414 8H17a1 1 0 110 2H4.414l3.293 3.293a1 1 0 010 1.414z" clipRule="evenodd" /></svg>
          다시 업로드하기
        </button>
        <button
          className="px-6 py-3 rounded-lg bg-green-600 text-white hover:bg-green-700 font-medium text-lg shadow-md transition duration-300 transform hover:scale-105"
          onClick={() => {
            if (typeof window !== 'undefined') {
              sessionStorage.setItem('resume_path', pdfUrl || '');
              sessionStorage.setItem('jd_text', JD || '');
            }
            window.location.href = '/evaluate';
          }}
        >
          📝 평가받기
        </button>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 좌측: 이력서 미리보기 */}
        <div className="bg-white rounded-lg shadow-md p-4 lg:h-[calc(100vh-8rem)] overflow-auto sticky top-4">
          <h2 className="text-lg font-semibold border-b pb-2 mb-4">📄 이력서</h2>
          {pdfError ? (
            <div className="border rounded p-4 bg-red-50 text-red-500">{pdfError}</div>
          ) : isPdf && pdfUrl ? (
            // PDF 미리보기는 한 번만 렌더링
            <PdfHighlighterView key={pdfUrl} pdfUrl={pdfUrl} />
          ) : thumbnailUrl ? (
            <img
              src={thumbnailUrl}
              alt="이력서 미리보기"
              className="w-full rounded"
            />
          ) : (
            <div className="border rounded p-4 bg-gray-50 text-gray-500 h-32 flex items-center justify-center">
              이력서 미리보기를 로드할 수 없습니다
            </div>
          )}
        </div>
        {/* 우측: 회사 정보, 분석 결과, 챗봇 */}
        <div className="space-y-6 lg:h-[calc(100vh-8rem)] overflow-auto">
          {/* 회사 정보 */}
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="flex items-center justify-between border-b pb-2 mb-4">
              <h2 className="text-lg font-semibold">🏢 {company || "Company Information"}</h2>
              {JD_url && (
                <a
                  href={JD_url}
                  className="text-blue-500 hover:text-blue-700 flex items-center"
                  target="_blank"
                  rel="noreferrer"
                >
                  <span>🔗 JD 원문</span>
                  <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
                  </svg>
                </a>
              )}
            </div>
            {JD ? (
              <div
                className="prose max-w-none"
                dangerouslySetInnerHTML={{
                  __html: DOMPurify.sanitize(marked(JD)),
                }}
              />
            ) : (
              <div className="flex items-center justify-center h-full text-gray-400">
                <p>채용 공고 정보를 로드 중입니다...</p>
              </div>
            )}
          </div>
          {/* 분석 결과 */}
          <div className="bg-white rounded-lg shadow-md p-4">
            <h2 className="text-lg font-semibold border-b pb-2 mb-4">🤖 Analysis Result</h2>
            {output ? (
              <div
                className="prose max-w-none"
                dangerouslySetInnerHTML={{
                  __html: DOMPurify.sanitize(marked(output)),
                }}
              />
            ) : (
              <div className="flex items-center justify-center h-full text-gray-400">
                <p>분석 결과를 로드 중입니다...</p>
              </div>
            )}
          </div>

          {/* user_resume 입력창: 분석결과와 챗봇 사이 */}
          <div className="bg-white rounded-lg shadow-md p-4 mb-4">
            <label htmlFor="user-resume-input" className="font-semibold mb-2 block">수정할 부분 입력하기</label>
            <textarea
              id="user-resume-input"
              className="w-full min-h-[120px] border border-gray-300 rounded-lg p-2 mb-2 focus:outline-none focus:ring-2 focus:ring-indigo-200"
              placeholder="수정이 필요한 이력서 내용을 붙여넣으세요."
              value={userResumeDraft}
              onChange={e => setUserResumeDraft(e.target.value)}
            />
            <div className="flex items-center justify-between">
              <button
                className="px-4 py-1 bg-indigo-600 text-white rounded hover:bg-indigo-700 transition mb-2"
                onClick={() => {
                  setUserResume(userResumeDraft);
                  if (typeof window !== 'undefined') {
                    window.localStorage.setItem('user_resume', userResumeDraft);
                  }
                }}
                disabled={userResumeDraft === userResume}
              >
                적용
              </button>
              <span className="text-xs text-gray-400 ml-2">* 이 내용은 변경 전까지 계속 사용됩니다.</span>
            </div>
          </div>
          {/* 챗봇 */}
          <section className="bg-white rounded-lg shadow-md p-4 mb-6 transition-all duration-300" id="chatbot-section">
            <h2 className="text-lg font-semibold border-b pb-2 mb-4">💬 Suggestion Agent</h2>
            <div className="flex flex-col space-y-4">
              <p className="text-gray-700">이력서를 개선하기 위한 질문이 있으신가요? 아래에 질문을 입력해주세요.</p>
              <div className="relative">
                <div 
                  className="border rounded-lg p-4 overflow-y-auto transition-all duration-500 ease-in-out"
                  id="chat-messages"
                  style={{ 
                    minHeight: '160px', 
                    maxHeight: '500px',
                    height: 'auto',
                    position: 'relative',
                    bottom: 0
                  }}
                >
                  <div className="mb-3 text-left">
                    <div className="inline-block px-4 py-2 rounded-lg bg-gray-200 text-gray-800 max-w-[90%]">
                      <div className="prose prose-sm" 
                        dangerouslySetInnerHTML={{
                          __html: DOMPurify.sanitize(marked("안녕하세요! 이력서 개선을 도와드릴게요. 분석 결과를 바탕으로 어떤 부분을 도와드릴까요?"))
                        }}
                      />
                    </div>
                  </div>
                </div>
              </div>
              <div className="flex">
                <input 
                  type="text" 
                  id="chat-input"
                  placeholder="질문을 입력하세요..."
                  className="flex-1 border rounded-l-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
                <button
                  id="send-message"
                  className="bg-indigo-600 text-white px-4 py-2 rounded-r-md hover:bg-indigo-700 focus:outline-none"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                </button>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};

export default ResultView;
