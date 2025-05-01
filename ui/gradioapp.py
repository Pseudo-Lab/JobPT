import gradio as gr
from PIL import Image
import requests
import tempfile
import markdown2
import uuid
import os
import io
import re
import fitz


def request_document_intelligence(image_path):
    url = "http://localhost:8000/matching"  # 실제 API 엔드포인트로 변경하세요.
    data = {"resume_path": image_path}

    try:
        response = requests.post(url, json=data)
        response.raise_for_status()  # 상태 코드가 200번대가 아니면 예외 발생
        print("POST 요청 성공:", response.json())
        res = response.json()
        return res["JD"], res["output"], res["JD_url"], res["name"]

    except requests.exceptions.RequestException as e:
        print("POST 요청 중 오류 발생:", e)


def save_file_temporarily(file_bytes, extension, directory):
    filename = f"{uuid.uuid4()}{extension}"
    filepath = os.path.join(directory, filename)
    with open(filepath, "wb") as f:
        f.write(file_bytes)
    return filepath


def get_google_drive_download_link(url):
    file_id_match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
    if file_id_match:
        file_id = file_id_match.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return url


def download_file(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, allow_redirects=True)
    if response.status_code != 200:
        raise Exception("Cannot download file.")
    return response.content


def process_local_file(file_path):
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension not in [".pdf", ".png", ".jpg", ".jpeg", ".gif"]:
        return "Not supported file type. Upload image or pdf."

    with tempfile.TemporaryDirectory() as temp_dir:
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        temp_file_path = save_file_temporarily(file_bytes, file_extension, temp_dir)

        result = request_document_intelligence(image_path=temp_file_path)
        return result[0], result[1], result[2], f"<h2>🏢 {result[3]}</h2>"


def analyze_cv(file):
    if file is None:
        return "select file."
    return process_local_file(file.name)


def analyze_from_url(url):
    if not url:
        return "Put URL"

    url = get_google_drive_download_link(url)

    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200:
            return "Cannot download file."
        file_bytes = response.content
    except Exception as e:
        return f"Error occured during URL downloading: {str(e)}"

    file_extension = os.path.splitext(url)[1].lower()
    if file_extension not in [".pdf", ".png", ".jpg", ".jpeg", ".gif"]:
        return "Not supported file type."

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = save_file_temporarily(file_bytes, file_extension, temp_dir)

        result = request_document_intelligence(temp_file_path)
        return result[0], result[1], result[2], f"<h2>🏢 {result[3]}</h2>"


def update_thumbnail(file_or_url):
    if file_or_url is None:
        return None

    try:
        if hasattr(file_or_url, "name"):
            file_extension = os.path.splitext(file_or_url.name)[1].lower()

            if file_extension in [".png", ".jpg", ".jpeg", ".gif"]:
                return Image.open(file_or_url.name)

            elif file_extension == ".pdf":
                try:
                    pdf_document = fitz.open(file_or_url.name)

                    page = pdf_document[0]
                    zoom = 4
                    mat = fitz.Matrix(zoom, zoom)
                    pix = page.get_pixmap(matrix=mat, alpha=False)

                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    pdf_document.close()
                    return img

                except Exception as pdf_error:
                    return None

            else:
                return None

        elif isinstance(file_or_url, (str, bytes)):
            url = get_google_drive_download_link(str(file_or_url))
            try:
                response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
                if response.status_code != 200:
                    return None

                file_extension = os.path.splitext(url)[1].lower()
                if file_extension in [".png", ".jpg", ".jpeg", ".gif"]:
                    return Image.open(io.BytesIO(response.content))
                elif file_extension == ".pdf":
                    pdf_document = fitz.open(stream=response.content, filetype="pdf")
                    page = pdf_document[0]
                    pix = page.get_pixmap(matrix=fitz.Matrix(4, 4))
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    pdf_document.close()
                    return img
            except Exception as e:
                print(f"URL 처리 중 오류: {e}")
                return None

    except Exception as e:
        print(f"전체 처리 중 오류: {e}")
        return None

    return None


custom_css = """
:root {
    --primary-bg: #1a1b1e;
    --secondary-bg: #2d2e32;
    --accent-color: #6366f1;
    --accent-hover: #818cf8;
    --text-primary: #e2e8f0;
    --text-secondary: #94a3b8;
    --border-color: #374151;
    --input-bg: #2d2e32;
    --success-color: #10b981;
    --error-color: #ef4444;
}

body, .gradio-container {
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    background-color: white;
    color: var(--text-primary);
    line-height: 1.5;
}

#cv-analysis-tool {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
}

#cv-analysis-tool h1 {
    font-size: 2rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 1.5rem;
    letter-spacing: -0.025em;
}

#cv-analysis-tool .gr-tabbed-interface {
    background-color: white;
    border-radius: 1rem;
    padding: 1.5rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

#cv-analysis-tool .tabs {
    border-bottom: 1px solid var(--border-color);
    margin-bottom: 1.5rem;
}

#cv-analysis-tool .tab-nav {
    padding: 0.75rem 1.25rem;
    color: var(--text-secondary);
    border-bottom: 2px solid transparent;
    transition: all 0.2s ease;
}

#cv-analysis-tool .tab-nav.selected {
    color: var(--accent-color);
    border-bottom-color: var(--accent-color);
}

#cv-analysis-tool .gr-textbox,
#cv-analysis-tool .gr-dropdown {
    background-color: white;
    border: 1px solid var(--border-color);
    border-radius: 0.5rem;
    padding: 0.75rem;
    color: var(--text-primary);
    transition: border-color 0.2s ease;
}
#custom-markdown {
    background-color: white;
    border-radius: 12px; /* 모서리를 둥글게 */
    padding: 20px; /* 내부 여백 */
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); /* 박스 그림자 */
}


#cv-analysis-tool .gr-textbox:focus,
#cv-analysis-tool .gr-dropdown:focus {
    border-color: var(--accent-color);
    outline: none;
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

#cv-analysis-tool .gr-button {
    background-color: var(--accent-color);
    color: #87ceeb;
    padding: 0.75rem 1.5rem;
    border-radius: 0.5rem;
    font-weight: 600;
    transition: all 0.2s ease;
    border: none;
    cursor: pointer;
}

#cv-analysis-tool .gr-button:hover {
    background-color: var(--accent-hover);
    transform: translateY(-1px);
}

#cv-analysis-tool .gr-button:active {
    transform: translateY(0);
}

#cv-analysis-tool .gr-image {
    border: 2px dashed var(--border-color);
    border-radius: 0.75rem;
    padding: 1.5rem;
    transition: border-color 0.2s ease;
}

#cv-analysis-tool .gr-image:hover {
    border-color: var(--accent-color);
}

#cv-analysis-tool .gr-textbox[label="Analysis Result"] {
    background-color: white;
    border: 1px solid var(--border-color);
    border-radius: 0.75rem;
    padding: 1rem;
    margin-top: 1rem;
    min-height: 200px;
}

@media (max-width: 768px) {
    #cv-analysis-tool {
        padding: 1rem;
    }
    
    #cv-analysis-tool .gr-tabbed-interface {
        padding: 1rem;
    }
    
    #cv-analysis-tool .gr-row {
        flex-direction: column;
    }
    
    #cv-analysis-tool .gr-button {
        width: 100%;
        margin-top: 1rem;
    }
}

#cv-analysis-tool .loading {
    opacity: 0.7;
    pointer-events: none;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

#cv-analysis-tool .gr-tab-content {
    animation: fadeIn 0.3s ease;
}

footer, 
header, 
.border-t, 
.absolute, 
.flex-col > .items-center, 
.gr-button:hover[data-testid="share-button"] {
    display: none !important;
}
"""

with gr.Blocks(title="JobPT", css=custom_css, elem_id="cv-analysis-tool") as demo:
    gr.Markdown("# 📄 JobPT (Assist you for Job Searching)")
    gr.Markdown("Upload your CV and click 'Analyze' to see the results.")

    with gr.Tab("💾 Upload CV"):
        gr.Markdown("Enter the CV URL (PDF or Image) and click 'Analyze from URL'.")
        with gr.Row():
            with gr.Column():
                input_file = gr.File(label="📎 Upload your CV (PDF or Image format)", file_types=[".pdf", ".png", ".jpg", ".jpeg", ".gif"])
            with gr.Column():
                upload_thumbnail = gr.Image(label="🖼️ Thumbnail Preview", height=480, interactive=False)
        with gr.Row():
            status_text = gr.Textbox(label="Status", value="Ready", interactive=False)
        with gr.Row():
            analyze_button = gr.Button("🔬 Analyze")
        with gr.Row():
            gr.Markdown("# 🔎 Job Description Result")
        with gr.Row():
            comopany_name_text = gr.Markdown(
                label="Company Name",
                show_copy_button=True,
            )
        with gr.Row():
            output_JD_text = gr.Markdown(label="🔎 Job Description Result", show_copy_button=True, elem_id="custom-markdown")
        with gr.Row():
            link_text = gr.Markdown(
                label="Link",
                show_copy_button=True,
            )
        with gr.Row():
            gr.Markdown("# 🤖 Analysis Result")
        with gr.Row():
            output_text = gr.Markdown(label="🤖 Analysis Result", show_copy_button=True, elem_id="custom-markdown")

        input_file.change(fn=update_thumbnail, inputs=[input_file], outputs=[upload_thumbnail])

        analyze_button.click(fn=lambda: "Processing...", outputs=status_text, queue=False).then(  # 시작할 때 상태 메시지
            fn=analyze_cv, inputs=[input_file], outputs=[output_JD_text, output_text, link_text, comopany_name_text]
        ).then(
            fn=lambda: "Complete!", outputs=status_text, queue=False  # 완료 메시지
        )

    with gr.Tab("📤 Analyze from URL"):
        gr.Markdown("Enter the CV URL (PDF or Image) and click 'Analyze from URL'.")
        with gr.Row():
            with gr.Column():
                url_textbox = gr.Textbox(label="📎 CV URL", scale=3)
            with gr.Column():
                url_thumbnail = gr.Image(label="🖼️ Thumbnail Preview", height=480, interactive=False)
        # URL 탭의 로딩 상태 표시
        with gr.Row():
            url_status_text = gr.Textbox(label="Status", value="Ready", interactive=False)
        with gr.Row():
            url_analyze_button = gr.Button("🔬 Analyze from URL")
        with gr.Row():
            gr.Markdown("# 🔎 Job Description Result")
        with gr.Row():
            comopany_name_url = gr.Markdown(
                label="Company Name",
                show_copy_button=True,
            )
        with gr.Row():
            output_JD_url = gr.Markdown(label="🔎 Job Description Result", show_copy_button=True, elem_id="custom-markdown")
        with gr.Row():
            link_url = gr.Markdown(
                label="Link",
                show_copy_button=True,
            )
        with gr.Row():
            gr.Markdown("# 🤖 Analysis Result")
        with gr.Row():
            output_text_url = gr.Markdown(label="🤖 Analysis Result", show_copy_button=True, elem_id="custom-markdown")

        url_textbox.change(fn=update_thumbnail, inputs=[url_textbox], outputs=[url_thumbnail])

        url_analyze_button.click(fn=lambda: "Processing...", outputs=url_status_text, queue=False).then(
            fn=analyze_from_url, inputs=[url_textbox], outputs=[output_JD_url, output_text_url, link_url, comopany_name_url]
        ).then(fn=lambda: "Complete!", outputs=url_status_text, queue=False)

    demo.launch(server_name="0.0.0.0", show_api=False)
