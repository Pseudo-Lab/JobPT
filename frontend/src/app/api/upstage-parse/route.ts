import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import os from "os";
import { spawnSync } from "child_process";

export const runtime = "nodejs"; // 파일 업로드 지원

export async function POST(req: NextRequest) {
    // 1. 파일 추출 및 임시 저장
    const formData = await req.formData();
    const file = formData.get("file") as File;
    if (!file) {
        return NextResponse.json({ error: "No file provided" }, { status: 400 });
    }
    const arrayBuffer = await file.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);

    // backend/uploaded_resumes 경로에 파일 저장
    const tmpFilename = `upload_${Date.now()}_${Math.random().toString(36).slice(2, 8)}_${file.name}`;
    const backendDir = path.join(process.cwd(), "..", "backend", "uploaded_resumes");
    
    // 디렉토리가 없으면 생성
    if (!fs.existsSync(backendDir)) {
        fs.mkdirSync(backendDir, { recursive: true });
    }
    
    const filePath = path.join(backendDir, tmpFilename);
    fs.writeFileSync(filePath, buffer);

    // public/uploads 경로에도 복사 (웹에서 접근 가능하도록)
    const publicDir = path.join(process.cwd(), "public", "uploads");
    if (!fs.existsSync(publicDir)) {
        fs.mkdirSync(publicDir, { recursive: true });
    }
    const publicFilePath = path.join(publicDir, tmpFilename);
    fs.copyFileSync(filePath, publicFilePath);
    const pdfUrl = `/uploads/${tmpFilename}`;

    // 2. 업로드된 파일을 upstage_parser.py로 파싱 (python에서 결과 저장)
    const pyPath = path.join(process.cwd(), "upstage_parser.py");
    const py = spawnSync("python3", [pyPath, filePath], { encoding: "utf-8" });

    // 3. 결과 확인 및 반환 (성공/실패만 반환)
    if (py.error) {
        console.error("[Python execution failed]", py.error);
        return NextResponse.json({ error: "Python execution failed", detail: String(py.error) }, { status: 500 });
    }
    if (py.status !== 0) {
        console.error("[Python script error]", py.stderr);
        console.error("[Python script stdout]", py.stdout);
        return NextResponse.json({ error: "Python script error", stderr: py.stderr, stdout: py.stdout }, { status: 500 });
    }

    // pdfUrl 추가하여 반환
    return NextResponse.json({ success: true, stdout: py.stdout, pdfUrl });
}
