from configs import UPSTAGE_API_KEY
import requests
import os

from typing import Optional, Dict, List
import io
import base64
from util.cv_format import create_structured_cv



# def process(image_input, box_threshold=0.05, iou_threshold=0.1, use_paddleocr=True, imgsz=640) -> Optional[Image.Image]:
#     print("1. process 함수 시작")
#     print("이미지 입력값:", type(image_input))
#     image_save_path = "imgs/saved_image_demo.png"
#     os.makedirs("imgs", exist_ok=True)
#     image_input.save(image_save_path)
#     image = Image.open(image_save_path)
#     box_overlay_ratio = image.size[0] / 3200
#     draw_bbox_config = {
#         "text_scale": 0.8 * box_overlay_ratio,
#         "text_thickness": max(int(2 * box_overlay_ratio), 1),
#         "text_padding": max(int(3 * box_overlay_ratio), 1),
#         "thickness": max(int(3 * box_overlay_ratio), 1),
#     }

#     ocr_bbox_rslt, is_goal_filtered = check_ocr_box(
#         image_save_path,
#         display_img=False,
#         output_bb_format="xyxy",
#         goal_filtering=None,
#         easyocr_args={"paragraph": False, "text_threshold": 0.9},
#         use_paddleocr=use_paddleocr,
#     )
#     text, ocr_bbox = ocr_bbox_rslt

#     dino_labled_img, label_coordinates, parsed_content_list = get_som_labeled_img(
#         image_save_path,
#         yolo_model,
#         BOX_TRESHOLD=box_threshold,
#         output_coord_in_ratio=True,
#         ocr_bbox=ocr_bbox,
#         draw_bbox_config=draw_bbox_config,
#         caption_model_processor=caption_model_processor,
#         ocr_text=text,
#         iou_threshold=iou_threshold,
#         imgsz=imgsz,
#     )
#     image = Image.open(io.BytesIO(base64.b64decode(dino_labled_img)))
#     print("parsed_content_list 타입:", type(parsed_content_list))
#     print(parsed_content_list)
#     print("첫 번째 항목:", parsed_content_list[0] if parsed_content_list else "비어있음")
#     # content 값들만 추출하여 문자열로 결합
#     parsed_content_list = "\n".join(item["content"] for item in parsed_content_list)
#     return image, parsed_content_list


# convert_pdf_to_jpg 함수는 더 이상 사용하지 않음 (PDF 직접 처리로 변경)
# def convert_pdf_to_jpg(pdf_path, output_folder):
#     image_paths = []
#     try:
#         # processed/images 하위에 저장
#         images_dir = os.path.join(output_folder, "images")
#         if not os.path.exists(images_dir):
#             os.makedirs(images_dir)
#
#         pdf_filename = os.path.splitext(os.path.basename(pdf_path))[0]
#         doc = fitz.open(pdf_path)
#
#         for i in range(doc.page_count):
#             page = doc.load_page(i)
#             pix = page.get_pixmap()
#             output_file = os.path.join(images_dir, f"{pdf_filename}_{i+1}.jpg")
#             pix.save(output_file)
#             print(f"페이지 {i+1}을(를) 저장했습니다: {output_file}")
#             image_paths.append(output_file)
#         print(f"변환 완료! 총 {doc.page_count} 페이지를 변환했습니다.")
#         return image_paths
#     except Exception as e:
#         print(f"에러가 발생했습니다: {str(e)}")

def run_parser(pdf_path):
    """
    Upstage API를 사용하여 PDF에서 텍스트를 추출합니다.
    """
    url = "https://api.upstage.ai/v1/document-digitization"
    headers = {"Authorization": f"Bearer {UPSTAGE_API_KEY}"}
    files = {"document": open(pdf_path, "rb")}
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
    elements = []

    for i in response_data['elements']:
        coordinates.append(i.get('coordinates'))
        elements.append(i)  # 전체 element 정보 저장
        contents.append(i['content'].get('markdown', ''))

    full_contents = response_data.get('content', {}).get('text', '')
    contents = "\n".join(contents)

    print(f"{pdf_path}에서 텍스트 추출 완료")
    return contents, coordinates, full_contents, elements


def run_parser_structured(pdf_path: str, return_structured: bool = True, use_llm: bool = True) -> Dict:
    """
    Upstage API를 사용하여 PDF에서 텍스트를 추출하고 구조화된 형태로 반환합니다.
    
    Args:
        pdf_path: PDF 파일 경로
        return_structured: True면 구조화된 형태로 반환, False면 기존 형식 반환
        use_llm: True면 LLM을 사용하여 구조화, False면 기본 파싱만 수행
    
    Returns:
        Dict (return_structured=True): {
            "raw_text": "전체 문자열",
            "structured": {
                "required": {
                    "basic_info": {...},
                    "summary": "...",
                    "experience": [...],
                    "education": [...],
                    "skills": [...],
                    "awards_certifications": [...],
                    "languages": [...],
                    "other_links": [...]
                },
                "optional": {
                    "unmapped_content": "...",
                    "additional_sections": {...}
                }
            },
            "elements": [...],
            "coordinates": [...]
        }
        또는
        Tuple (return_structured=False): (contents, coordinates, full_contents, elements)
    """
    # 기존 파서 실행
    contents, coordinates, full_contents, elements = run_parser(pdf_path)
    
    # 구조화된 형태로 변환
    if return_structured:
        structured_result = create_structured_cv(
            raw_text=contents,
            elements=elements,
            coordinates=coordinates,
            language=None,  # 자동 감지
            use_llm=use_llm
        )
        return structured_result
    else:
        # 기존 형식 유지 (하위 호환성)
        return contents, coordinates, full_contents, elements

