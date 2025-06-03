import re
from datetime import datetime
from pathlib import Path
from configs import UPSTAGE_API_KEY
import requests
from pdf2image import convert_from_path
import fitz  # PyMuPDF
import os

from typing import Optional
from PIL import Image
import io
import base64
import matplotlib.pyplot as plt
from dotenv import load_dotenv
load_dotenv()

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
    api_key = UPSTAGE_API_KEY
    print(api_key)
    print(image_path)
    
    url = "https://api.upstage.ai/v1/document-digitization"
    headers = {"Authorization": f"Bearer {api_key}"}
    files = {"document": open(image_path, "rb")}
    data = {
        "ocr": "force",
        "base64_encoding": "['table']",
        "model": "document-parse",
        "output_formats": "['markdown', 'text']"
    }

    response = requests.post(url, headers=headers, files=files, data=data)

    # ✅ 응답 검사
    try:
        response_data = response.json()
    except Exception as e:
        print(" JSON 파싱 실패:", e)
        print("응답 원문:", response.text)
        raise Exception("Upstage API 응답이 JSON 형식이 아닙니다")

    if response.status_code != 200:
        print("Upstage API 요청 실패")
        print("Status Code:", response.status_code)
        print("응답:", response_data)
        raise Exception("Upstage API 요청 실패")

    if 'elements' not in response_data:
        print("'elements' 키가 응답에 없음:", response_data)
        raise Exception("Upstage 응답에 elements 키 없음")

    coordinates = []
    contents = []

    for i in response_data['elements']:
        coordinates.append(i['coordinates'])
        contents.append(i['content'].get('markdown', ''))

    full_contents = response_data.get('content', {}).get('text', '')
    contents = "\n".join(contents)

    return contents, coordinates, full_contents

