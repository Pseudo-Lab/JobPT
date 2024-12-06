import numpy as np
import torch
import logging
import json
import os
import re
from datetime import datetime
from pathlib import Path

import pdfplumber
from pdf2image import convert_from_path
import pytesseract

import docx
import cv2

import spacy
from transformers import pipeline
print(np.__version__)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"사용하는 장치: {device}")

import os
print("현재 위치:", os.getcwd())

if str(os.getcwd()[-10:]) != "OmniParser":
    os.chdir('OmniParser')
    print("변경된 위치:", os.getcwd())

from typing import Optional
import numpy as np
import torch
from PIL import Image
import io
import base64
import os
import matplotlib.pyplot as plt

from utils import check_ocr_box, get_yolo_model, get_caption_model_processor, get_som_labeled_img

yolo_model = get_yolo_model(model_path='weights/icon_detect/best.pt')
caption_model_processor = get_caption_model_processor(
    model_name="florence2", model_name_or_path="weights/icon_caption_florence"
)

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

def process(
    image_input,
    box_threshold=0.05,
    iou_threshold=0.1,
    use_paddleocr=True,
    imgsz=640
) -> Optional[Image.Image]:
    image_save_path = 'imgs/saved_image_demo.png'
    os.makedirs('imgs', exist_ok=True)
    image_input.save(image_save_path)
    image = Image.open(image_save_path)
    box_overlay_ratio = image.size[0] / 3200
    draw_bbox_config = {
        'text_scale': 0.8 * box_overlay_ratio,
        'text_thickness': max(int(2 * box_overlay_ratio), 1),
        'text_padding': max(int(3 * box_overlay_ratio), 1),
        'thickness': max(int(3 * box_overlay_ratio), 1),
    }

    ocr_bbox_rslt, is_goal_filtered = check_ocr_box(
        image_save_path,
        display_img=False,
        output_bb_format='xyxy',
        goal_filtering=None,
        easyocr_args={'paragraph': False, 'text_threshold': 0.9},
        use_paddleocr=use_paddleocr
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
        imgsz=imgsz
    )
    image = Image.open(io.BytesIO(base64.b64decode(dino_labled_img)))
    parsed_content_list = '\n'.join(parsed_content_list)
    return image, parsed_content_list

def run_parser(image_path):


    box_threshold = 0.05 
    iou_threshold = 0.1 
    use_paddleocr = True 
    imgsz = 640

    # image_path = "../data/sample_page_2.jpg"
    image_input = Image.open(image_path).convert('RGB')

    output_image, parsed_content = process(
        image_input,
        box_threshold,
        iou_threshold,
        use_paddleocr,
        imgsz
    )

    print('Parsed Screen Elements:')
    print(parsed_content)

    plt.figure(figsize=(10,10))
    plt.imshow(output_image)
    plt.axis('off')
    plt.show()

    print("현재 위치:", os.getcwd())

    if str(os.getcwd()[-10:]) == "OmniParser":
        os.chdir('..')
        print("변경된 위치:", os.getcwd())

    lines = parsed_content.split('\n')

    texts = []
    for line in lines:
        if ':' in line:
            text = line.split(':', 1)[1].strip()
            texts.append(text)

    processed_texts = []
    i = 0
    while i < len(texts):
        text = texts[i]
        if text.endswith('-'):
            text = text[:-1]
            if i + 1 < len(texts):
                text += texts[i + 1]
                i += 1
        processed_texts.append(text)
        i += 1

    combined_text = ' '.join(processed_texts)

    sentence_endings = re.compile(r'(?<=[.!?]) +')
    sentences = sentence_endings.split(combined_text)

    paragraphs = []
    current_paragraph = ''
    for sentence in sentences:
        headings = ['Education', 'Publications', 'Honors', 'Relevant Courses', 'GPA', 'Advisor', 'Minor', 'Email', 'Research Advisor']
        if any(heading in sentence for heading in headings):
            if current_paragraph:
                paragraphs.append(current_paragraph.strip())
            current_paragraph = sentence.strip() + ' '
        else:
            current_paragraph += sentence.strip() + ' '

    if current_paragraph:
        paragraphs.append(current_paragraph.strip())

    for para in paragraphs:
        print(para)
        print('\n')

    return "\n".join(paragraphs)