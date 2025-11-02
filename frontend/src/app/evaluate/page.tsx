// src/app/evaluate/page.tsx
"use client";

import Link from 'next/link';
import { useEffect, useState } from 'react';


export default function EvaluatePage() {
  // basic.html fetch
  const [html, setHtml] = useState('');
  const [loading, setLoading] = useState(true);
  const [progress, setProgress] = useState(0);
  const [stepMsg, setStepMsg] = useState('분석 준비 중...');
  const [error, setError] = useState('');

  useEffect(() => {
    setLoading(true);
    setError('');
    setProgress(0);
    setStepMsg('이력서 추출 중...');

    // 프로그레스 및 단계 메시지 시뮬레이션 (실제 진행상황과 동기화하고 싶으면 백엔드에서 단계별 메시지 반환 필요)
    const steps = [
      { p: 10, msg: '이력서 추출 중...' },
      { p: 30, msg: '채용공고 분석 중...' },
      { p: 50, msg: '키워드 매칭 분석 중...' },
      { p: 65, msg: '경험/자격 분석 중...' },
      { p: 80, msg: '최종 점수 및 개선점 생성 중...' },
      { p: 95, msg: 'HTML 리포트 생성 중...' },
    ];
    let stepIdx = 0;
    const interval = setInterval(() => {
      if (stepIdx < steps.length) {
        setProgress(steps[stepIdx].p);
        setStepMsg(steps[stepIdx].msg);
        stepIdx++;
      }
    }, 12000); // 1.2초마다 단계 진행 (전체 약 7초)

    // 이력서 경로와 JD 텍스트를 sessionStorage에서 가져오거나, fallback 값 사용
    const resumePath = typeof window !== "undefined" ? sessionStorage.getItem('resume_path') : null;
    const jdText = typeof window !== "undefined" ? sessionStorage.getItem('jd_text') : null;
    if (!resumePath || !jdText) {
      setError('이력서 또는 채용공고 정보가 없습니다. 이전 단계에서 업로드/분석을 완료해주세요.');
      setLoading(false);
      clearInterval(interval);
      return;
    }
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/evaluate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resume_path: resumePath, jd_text: jdText, model: 1 })
    })
      .then(async (res) => {
        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          throw new Error(data.detail || data.error || '서버 오류');
        }
        return res.json();
      })
      .then((data) => {
        setHtml(data.html);
        setProgress(100);
        setStepMsg('분석 완료!');
      })
      .catch((err) => setError(err.message))
      .finally(() => {
        setLoading(false);
        clearInterval(interval);
      });
  }, []);


  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">📝 Evaluate Page</h1>
      <div className="mb-6">
        <h2 className="text-lg font-semibold mb-2">기본 리포트 (Basic Report)</h2>
        <div className="border rounded bg-white p-4 shadow mb-4 prose max-w-none">
          {loading ? (
              <>
                <div className="flex flex-col items-center w-full mb-2">
                  <img src="/logo/loading.gif" alt="loading" style={{ height: 48, width: 'auto' }} className="mb-3" />
                  <div className="h-3 bg-gray-200 rounded-full overflow-hidden w-full">
                    <div className="bg-green-500 h-3 transition-all duration-700" style={{ width: `${progress}%` }} />
                  </div>
                  <div className="mt-2 text-center text-sm text-gray-600 animate-pulse">{stepMsg}</div>
                </div>
                <div className="text-center text-gray-400 mt-3">리포트 생성에는 수십 초~수 분이 소요될 수 있습니다.<br/>잠시만 기다려주세요...</div>
              </>
            ) : error ? (
            <div className="text-red-600">{error}</div>
          ) : (
            <>
              <div dangerouslySetInnerHTML={{ __html: html }} />
              <div className="flex justify-end mt-4">
                <button
                  className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                  onClick={() => {
                    const blob = new Blob([html], { type: 'text/html' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'ats_report.html';
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                  }}
                >
                  리포트 다운로드
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      <div className="mt-6">
        <Link href="/">
          <button className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300">
            ← 메인으로 돌아가기
          </button>
        </Link>
      </div>
    </div>
  );
}