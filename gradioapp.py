import gradio as gr
from PIL import Image
import requests
import fitz
import io
import tempfile
import uuid
import os
import re

def request_document_intelligence(image_path):
    """
    input: file_path
    output: string
    """
    # endpoint = f""
    
    # params = {

    # }
    
    # headers = {
    #     "api-Key": ""
    # }    
    
    # is_url = False
    
    # if image_path.startswith("http"):
    #     is_url = True
    
    # if is_url:
    #     payload = "{'urlSource': '" + image_path + "'}"
    # else:
    #     with open(image_path, "rb") as image:
    #         payload = image.read()
    #     headers.update({"Content-Type": "image/*"})
        
    # response = requests.post(endpoint, params=params, headers=headers, data=payload)
    
    # print("RESPONSE1 : ", response, response.elapsed.total_seconds())
    # if response.status_code == 202:
    #     result_url = response.headers['Operation-Location']
        
    #     while(1):
    #         result_response = requests.get(result_url, headers=headers)
    #         result_response_json = result_response.json()
    #         current_status = result_response_json['status']
    #         print("RESPONSE2 : ", result_response.json())
    #         if current_status == 'running':
    #             print(current_status, result_response.elapsed.total_seconds())
    #             time.sleep(1)
    #             continue
    #         else:
    #             break

    #     if current_status == "succeeded":
    #         print(result_response_json)
    #         return result_response_json
    #     else:
    #         return None
    # return None
    return "good"

def save_image_temporarily(image, directory):
    if image.mode != 'RGB':
        image = image.convert('RGB')
    filename = f"{uuid.uuid4()}.jpg"
    filepath = os.path.join(directory, filename)
    image.save(filepath, "JPEG")
    return filepath

def convert_pdf_to_image_paths_from_bytes(pdf_bytes, temp_dir):
    image_paths = []
    try:
        pdf_document = fitz.open("pdf", pdf_bytes)
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            zoom = 2
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            img_path = save_image_temporarily(img, temp_dir)
            image_paths.append(img_path)
        pdf_document.close()
        return image_paths
    except Exception as e:
        print(f"Error occured during PDF conversion: {e}")
        return []

def get_google_drive_download_link(url):
    file_id_match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
    if file_id_match:
        file_id = file_id_match.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return url

def download_file(url):
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    response = requests.get(url, headers=headers, allow_redirects=True)
    if response.status_code != 200:
        raise Exception("Cannot download file.")
    return response.content

def determine_file_type(file_bytes):
    try:
        img = Image.open(io.BytesIO(file_bytes))
        img.verify()  
        img.close()
        return 'image'
    except:
        pass
    
    try:
        pdf_document = fitz.open("pdf", file_bytes)
        if pdf_document.page_count > 0:
            pdf_document.close()
            return 'pdf'
        pdf_document.close()
    except:
        pass
    
    return 'unknown'

def process_local_file(file_path):
    with open(file_path, 'rb') as f:
        file_bytes = f.read()
        
    file_type = determine_file_type(file_bytes)

    with tempfile.TemporaryDirectory() as temp_dir:
        if file_type == 'pdf':
            image_paths = convert_pdf_to_image_paths_from_bytes(file_bytes, temp_dir)
            if not image_paths:
                return "Error occured during PDF processing"
        elif file_type == 'image':
            try:
                img = Image.open(io.BytesIO(file_bytes))
                image_paths = [save_image_temporarily(img, temp_dir)]
                img.close()
            except Exception as e:
                return f"Error occured during image processing: {str(e)}"
        else:
            return "Not supported file type. Upload image or pdf."
        
        results = []
        for img_path in image_paths:
            result = request_document_intelligence(image_path=img_path)
            results.append(result)
        
        if len(results) == 1:
            return results[0]
        else:
            return "\n\n=== === === === ===\n\n".join(results)

def analyze_cv(file):
    if file is None:
        return "select file."
    return process_local_file(file.name)

def analyze_from_url(url):
    if not url:
        return "Put URL"
    
    url = get_google_drive_download_link(url)
    
    try:
        file_bytes = download_file(url)
    except Exception as e:
        return f"Error occured during URL downloading: {str(e)}"
    
    file_type = determine_file_type(file_bytes)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        if file_type == 'pdf':
            image_paths = convert_pdf_to_image_paths_from_bytes(file_bytes, temp_dir)
            if not image_paths:
                return "Error occured during PDF processing."
        elif file_type == 'image':
            try:
                img = Image.open(io.BytesIO(file_bytes))
                image_paths = [save_image_temporarily(img, temp_dir)]
                img.close()
            except Exception as e:
                return f"Error occured during image processing: {str(e)}"
        else:
            return "Not support file type or cannot processing the file"
        
        results = []
        for img_path in image_paths:
            result = request_document_intelligence(image_path=img_path)
            results.append(result)
        
        if len(results) == 1:
            return results[0]
        else:
            return "\n\n=== === === === ===\n\n".join(results)

def update_url_thumbnail(url):
    if not url:
        return None
    
    url = get_google_drive_download_link(url)
    
    try:
        file_bytes = download_file(url)
    except:
        return None
    
    file_type = determine_file_type(file_bytes)
    
    if file_type == 'image':
        try:
            img = Image.open(io.BytesIO(file_bytes))
            return img
        except:
            return None
    elif file_type == 'pdf':
        try:
            pdf_document = fitz.open("pdf", file_bytes)
            page = pdf_document[0]
            zoom = 2
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            pdf_document.close()
            return img
        except:
            return None
    else:
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
    background-color: var(--primary-bg);
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
    background-color: var(--secondary-bg);
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
    background-color: var(--input-bg);
    border: 1px solid var(--border-color);
    border-radius: 0.5rem;
    padding: 0.75rem;
    color: var(--text-primary);
    transition: border-color 0.2s ease;
}

#cv-analysis-tool .gr-textbox:focus,
#cv-analysis-tool .gr-dropdown:focus {
    border-color: var(--accent-color);
    outline: none;
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

#cv-analysis-tool .gr-button {
    background-color: var(--accent-color);
    color: white;
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
    background-color: var(--secondary-bg);
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
    gr.Markdown("# JobPT (Assist you for applying job)")
    gr.Markdown("Upload your CV and click 'Analyze' to see the results.")
    
    with gr.Tab("Upload CV"):
        with gr.Row():
            with gr.Column():
                input_file = gr.File(
                    label="Upload your CV (PDF or Image format)", 
                    file_types=['.pdf', '.png', '.jpg', '.jpeg', '.gif']
                )
                analyze_button = gr.Button("Analyze")
            with gr.Column():
                gr.Markdown("### Analysis Result")
                output_text = gr.Textbox(label="Analysis Result", interactive=False)
        
        analyze_button.click(fn=analyze_cv,
                             inputs=[input_file],
                             outputs=[output_text])
    
    with gr.Tab("Analyze from URL"):
        gr.Markdown("Enter the CV URL (PDF or Image) and click 'Analyze from URL'.")
        with gr.Row():
            with gr.Column():
                url_textbox = gr.Textbox(label="CV URL", scale=3)
                url_analyze_button = gr.Button("Analyze from URL", scale=1)
            with gr.Column():
                url_thumbnail = gr.Image(label="Thumbnail Preview", height=200, interactive=False)
                gr.Markdown("### URL Analysis Result")
        output_text_url = gr.Textbox(label="Analysis Result", interactive=False)
                
        url_textbox.change(fn=update_url_thumbnail, inputs=[url_textbox], outputs=[url_thumbnail])
        url_analyze_button.click(fn=analyze_from_url, inputs=[url_textbox], outputs=[output_text_url])
    
    demo.launch(show_api=False)