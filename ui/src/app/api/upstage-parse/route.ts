import { NextRequest, NextResponse } from "next/server";

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

    // 임시 경로와 public/uploads 경로에 파일 저장
    const fs = require("fs");
    const path = require("path");
    const os = require("os");
    const { spawnSync } = require("child_process");
    const tmpDir = os.tmpdir();
    const tmpFilename = `upload_${Date.now()}_${Math.random().toString(36).slice(2, 8)}_${file.name}`;
    const tmpFilePath = path.join(tmpDir, tmpFilename);
    fs.writeFileSync(tmpFilePath, buffer);

    // public/uploads 경로에도 복사 (Next.js에서 public은 process.cwd()/public)
    const uploadsDir = path.join(process.cwd(), "public", "uploads");
    if (!fs.existsSync(uploadsDir)) {
        fs.mkdirSync(uploadsDir, { recursive: true });
    }
    const publicFilePath = path.join(uploadsDir, tmpFilename);
    fs.copyFileSync(tmpFilePath, publicFilePath);
    const pdfUrl = `/uploads/${tmpFilename}`;

    // 2. 업로드된 파일을 upstage_parser.py로 파싱 (python에서 결과 저장)
    const pyPath = path.join(process.cwd(), "upstage_parser.py");
    const py = spawnSync("python3", [pyPath, tmpFilePath], { encoding: "utf-8" });

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
