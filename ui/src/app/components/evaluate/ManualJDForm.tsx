import React, { useState } from "react";
import { ManualJDFormProps } from "../types/evaluate";

const ManualJDForm: React.FC<ManualJDFormProps> = ({ onSubmit, onBack }) => {
  const [company, setCompany] = useState("");
  const [jdUrl, setJDUrl] = useState("");
  const [jdText, setJDText] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(company, jdUrl, jdText);
  };

  return (
    <div className="max-w-lg mx-auto p-6 bg-white rounded-lg shadow-md mt-8">
      <button className="mb-4 text-indigo-600 hover:underline" onClick={onBack}>
        ← 뒤로가기
      </button>
      <h2 className="text-2xl font-bold mb-4">JD 정보 입력</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">회사명</label>
          <input
            type="text"
            value={company}
            onChange={e => setCompany(e.target.value)}
            className="w-full border rounded-md px-3 py-2"
            placeholder="예: 카카오"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">JD 링크</label>
          <input
            type="url"
            value={jdUrl}
            onChange={e => setJDUrl(e.target.value)}
            className="w-full border rounded-md px-3 py-2"
            placeholder="예: https://company.com/job/123"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">JD 내용</label>
          <textarea
            value={jdText}
            onChange={e => setJDText(e.target.value)}
            className="w-full border rounded-md px-3 py-2 min-h-[120px]"
            placeholder="JD 텍스트를 붙여넣어 주세요"
            required
          />
        </div>
        <button
          type="submit"
          className="w-full py-2 px-4 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
        >
          입력 완료
        </button>
      </form>
    </div>
  );
};

export default ManualJDForm;
