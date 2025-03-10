import numpy as np
import torch
import os
import re
from datetime import datetime
from pathlib import Path

from pdf2image import convert_from_path

import fitz  # PyMuPDF

print(np.__version__)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"사용하는 장치: {device}")

import os

print("현재 위치:", os.getcwd())

from typing import Optional
import numpy as np
import torch
from PIL import Image
import io
import base64
import os
import matplotlib.pyplot as plt

from OmniParser_v1.utils import check_ocr_box, get_yolo_model, get_caption_model_processor, get_som_labeled_img

yolo_model = get_yolo_model(model_path="system/OmniParser_v1/weights/icon_detect/best.pt")
caption_model_processor = get_caption_model_processor(model_name="florence2", model_name_or_path="system/OmniParser_v1/weights/icon_caption_florence")

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def process(image_input, box_threshold=0.05, iou_threshold=0.1, use_paddleocr=True, imgsz=640) -> Optional[Image.Image]:
    print("1. process 함수 시작")
    print("이미지 입력값:", type(image_input))
    image_save_path = "imgs/saved_image_demo.png"
    os.makedirs("imgs", exist_ok=True)
    image_input.save(image_save_path)
    image = Image.open(image_save_path)
    box_overlay_ratio = image.size[0] / 3200
    draw_bbox_config = {
        "text_scale": 0.8 * box_overlay_ratio,
        "text_thickness": max(int(2 * box_overlay_ratio), 1),
        "text_padding": max(int(3 * box_overlay_ratio), 1),
        "thickness": max(int(3 * box_overlay_ratio), 1),
    }

    ocr_bbox_rslt, is_goal_filtered = check_ocr_box(
        image_save_path,
        display_img=False,
        output_bb_format="xyxy",
        goal_filtering=None,
        easyocr_args={"paragraph": False, "text_threshold": 0.9},
        use_paddleocr=use_paddleocr,
    )
    text, ocr_bbox = ocr_bbox_rslt

    dino_labled_img, label_coordinates, parsed_content_list = get_som_labeled_img(
        image_save_path,
        yolo_model,
        BOX_TRESHOLD=box_threshold,
        output_coord_in_ratio=True,
        ocr_bbox=ocr_bbox,
        draw_bbox_config=draw_bbox_config,
        caption_model_processor=caption_model_processor,
        ocr_text=text,
        iou_threshold=iou_threshold,
        imgsz=imgsz,
    )
    image = Image.open(io.BytesIO(base64.b64decode(dino_labled_img)))
    print("parsed_content_list 타입:", type(parsed_content_list))
    print(parsed_content_list)
    print("첫 번째 항목:", parsed_content_list[0] if parsed_content_list else "비어있음")
    # content 값들만 추출하여 문자열로 결합
    parsed_content_list = "\n".join(item["content"] for item in parsed_content_list)
    return image, parsed_content_list


def convert_pdf_to_jpg(pdf_path, output_folder):
    image_paths = []
    try:
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        pdf_filename = os.path.splitext(os.path.basename(pdf_path))[0]
        doc = fitz.open(pdf_path)

        for i in range(doc.page_count):
            page = doc.load_page(i)
            pix = page.get_pixmap()
            output_file = os.path.join(output_folder, f"{pdf_filename}_{i+1}.jpg")
            pix.save(output_file)
            print(f"페이지 {i+1}을(를) 저장했습니다: {output_file}")
            image_paths.append(output_file)
        print(f"변환 완료! 총 {doc.page_count} 페이지를 변환했습니다.")
        return image_paths
    except Exception as e:
        print(f"에러가 발생했습니다: {str(e)}")


def run_parser(image_path):
    print("image_path")
    print(image_path)
    box_threshold = 0.05
    iou_threshold = 0.1
    use_paddleocr = True
    imgsz = 640

    # image_path = "../data/sample_page_2.jpg"
    image_input = Image.open(image_path).convert("RGB")

    output_image, parsed_content = process(image_input, box_threshold, iou_threshold, use_paddleocr, imgsz)

    print("Parsed Screen Elements:")
    print(parsed_content)

    # plt.figure(figsize=(10, 10))
    # plt.imshow(output_image)
    # plt.axis("off")
    # plt.show()

    print("현재 위치:", os.getcwd())

    # if str(os.getcwd()[-10:]) == "OmniParser":
    #     os.chdir("..")
    #     print("변경된 위치:", os.getcwd())

    lines = parsed_content.split("\n")

    texts = []
    for line in lines:
        if ":" in line:
            text = line.split(":", 1)[1].strip()
            texts.append(text)

    processed_texts = []
    i = 0
    while i < len(texts):
        text = texts[i]
        if text.endswith("-"):
            text = text[:-1]
            if i + 1 < len(texts):
                text += texts[i + 1]
                i += 1
        processed_texts.append(text)
        i += 1

    combined_text = " ".join(processed_texts)

    sentence_endings = re.compile(r"(?<=[.!?]) +")
    sentences = sentence_endings.split(combined_text)

    paragraphs = []
    current_paragraph = ""
    for sentence in sentences:
        headings = ["Education", "Publications", "Honors", "Relevant Courses", "GPA", "Advisor", "Minor", "Email", "Research Advisor"]
        if any(heading in sentence for heading in headings):
            if current_paragraph:
                paragraphs.append(current_paragraph.strip())
            current_paragraph = sentence.strip() + " "
        else:
            current_paragraph += sentence.strip() + " "

    if current_paragraph:
        paragraphs.append(current_paragraph.strip())

    for para in paragraphs:
        print(para)
        print("\n")

    return "\n".join(paragraphs)
