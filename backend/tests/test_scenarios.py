"""
JobPT 테스트 시나리오 기반 자동 테스트
CSV 파일의 모든 테스트 시나리오를 검증합니다.

실행 방법:
pytest backend/tests/test_scenarios.py -v
pytest backend/tests/test_scenarios.py::TestMandatoryScenarios -v
pytest backend/tests/test_scenarios.py -k "필수" -v
"""

import pytest
import csv
import time
import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.multi_agents.graph import create_graph
from backend.multi_agents.states.states import State, get_session_state, end_session, session_states
from langchain_core.messages import HumanMessage


# ==================== CSV 데이터 로드 ====================


def load_test_scenarios(csv_path: str) -> List[Dict]:
    """CSV 파일에서 테스트 시나리오 로드"""
    scenarios = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            scenarios.append(row)
    return scenarios


@pytest.fixture(scope="module")
def test_scenarios():
    """테스트 시나리오 데이터 로드"""
    csv_path = "/Users/manchann/Desktop/programming/JobPT/JobPT_test_scenarios - test_scenarios.csv"
    return load_test_scenarios(csv_path)


@pytest.fixture
def sample_resume():
    """테스트용 샘플 이력서 - 최재강 ML Engineer"""
    return """
이력서 - ML Engineer / 최재강

Contact
Email | workd.official@gmail.com
Phone Number | 01090406282
Portfolio | 포트폴리오 - ML Engineer / 최재강
Github | https://github.com/workdd
LinkedIn | https://www.linkedin.com/in/jg-choi
Tech Blog | https://manchann.tistory.com

Introduction
2년차 ML Engineer(전문연구요원)로 현재 재직중이며, LLM 서비스 기능 구현 및 추론 최적화 업무를 주로 담당하고 있습니다.
기존의 것보다 더 최선의 방법이 있다면 적극적으로 수용하는 것을 좋아합니다.
함께 일하는 사람들과 같이 성장해 나가는 것에 큰 성취감을 느낍니다.
ML 외에도 K8s 운영, API 배포에 대한 이해와 경험이 있습니다.
전문연구요원 전직을 희망합니다.(2025.08.07부터 전직 가능)

Career
• 오케스트로 ML Engineer (2023.08 ~ Present)
• 국민대학교 컴퓨터공학과 석사 (2021.09 ~ 2023.08)
• 국민대학교 소프트웨어학부 학사 (2017.03 ~ 2021.08)

Experience

오케스트로 | ML Engineer (2023.08 ~ Present)

클라리넷, 폐쇄망 LLM 서비스 개발 및 고도화

LLM 시스템 추론 성능 최적화
• 기존 HF Transformers 기준 추론 환경에서 vLLM 프레임워크를 사용하여 PagedAttention 및 Continuous Batching 기반 비동기 추론 API 구현
• Nvidia A100 40GB 1대와 14B모델 기준, 기존 Transformers 기반 추론 환경은 2배치까지 추론이 가능했으나, 최대 20배치 지원 및 총 추론 시간 40배 성능 증가
• 동일한 vLLM 추론 환경에서, CUDA Graph Capturing, Prefix Caching, Chunked Prefill 기법 적용 및 GPTQ 양자화 방법 변경 제안으로 단일 배치 기준 6.18배 성능을 증가시킴
• 상반기 사내 목표인 최대 동시 추론 3이상, 100개의 추론에 대한 총 추론 시간을 13분 이내로 단축하는 미션을 최대 동시 추론 20개, 100개의 추론에 대해 2분 이내 달성으로 목표 초과 달성함

성과: LLM 시스템 추론 속도 향상 기여로, 클라리넷은 GS 소프트웨어 품질 1등급 인증을 받게 됨

회사 QA 홈페이지 챗봇 개발
• sLLM 기반 추론 속도 최적화: GCP L4 24GB GPU환경에서 동시 추론 5, 10초 내 응답 시작 목표
• Gemma 4B, QLoRA기반 양자화 모델 사용, LoRA Adapter 병합 및 GPTQ 기반 재양자화를 통해 정확도 저하 없이, vLLM 추론 속도 극대화
• 단일 배치 기준 평균 45tps 제공 및 배치 5기준 평균 4.3초내 답변 성능 달성

한국행정연구원 보고서 목차별 요약 POC
• 목차별 요약 결과 취합 후 LLM을 이용한 통합 작업을 진행하여 요약 내용의 통일성 향상
• LLM-as-a-Judge 기법을 통한 요약 성능 평가 및 성능 점수화를 통해 내부 평가 결과 요약 성능이 초기 60점에서 85점으로 상승
• 기존 Transformer 방법에서 vLLM 라이브러리 적용을 통해 평균 추론 시간 3.2배 향상
• GPU 병렬 처리를 통해 단일 GPU 추론 대비 1.8배 성능 향상

LLM 외국어 Block LogitProcessor 구현
• Qwen2.5 모델의 중국어 랜덤 출력 문제 해결
• LLM 추론 시 중국어, 러시아어 등 외국어에 대한 Logit 값을 -inf 처리하여, 의도하지 않은 외국어 출현 문제를 해결
• 사내 QA 데이터셋 기준 중국어 발현 비율이 기존 8%에서 0%로 수렴
• 해당 내용을 리포트 및 오픈 소스로 공유

Project

가짜연구소 러너 활동 (2024.10 ~ Present)
이력서 기반 모집 공고 추천 및 수정 제안 서비스
• LangGraph 기반 Multi-Agent 이력서 피드백 챗봇 개발
• FastAPI 기반 Multi-Agent 멀티턴 답변 API 구현
• Supervisor Agent를 통한 유저 채팅 입력별 Agent 라우팅 기능 구현
• LangFuse를 통해 Agent State 파악 및 디버깅

성과: 프로토타입 시연 발표 및 2025 PseudoCon에 참여하여 데모 부스 운영

Certification
• CKA(Certified Kubernetes Administrator)
• AWS Practitioner

Technical Skills
• ML/DL: PyTorch, vLLM, GPTQ, LangGraph, LangChain
• Programming: Python, FastAPI, API 배포
• Infrastructure: Kubernetes, GCP, GPU 최적화
"""


@pytest.fixture
def coupang_jd():
    """쿠팡 Data Scientist 직무 설명"""
    return """
회사 소개
쿠팡은 고객 감동 실현을 위해 존재합니다. 고객이 "쿠팡 없이 어떻게 살았을까?"라고 말할 때 쿠팡은 옳은 일을 하고 있다고 느낍니다.
쿠팡은 가장 빠르게 성장하고 있는 이커머스 기업으로, 한국 시장에서 강력하고 신뢰할 수 있는 기업으로 독보적인 명성을 쌓았습니다.
쿠팡은 스타트업 문화를 기반으로 한 글로벌 대형 상장사라고 자부합니다.

팀 소개
CCP(Customer-Centric Planning)팀에서는 '고객의 소리'를 바탕으로 고객경험을 저해시키는 요소를 제거하거나 기존 경험을 10배 이상 개선하는 미션을 가지고 전사의 모든 조직과 협업을 합니다.
CCP팀의 Data Scientist는 데이터와 과학을 바탕으로 의사결정권자에게 Insight를 제공하고 문제해결에 일조합니다.

주요업무
• 최첨단 AI 모델 및 방법론을 적용하여 비즈니스 니즈 및 문제 해결
• LLM 모델 구축, POC 수행 및 최적화하여 프로덕션에 배포
• 생성형 AI를 활용한 최첨단 솔루션의 설계, 전파 및 구현

자격요건
• 최소 5년 이상의 데이터 과학/공학 또는 통계학 관련 분야 경력
• Python 관련 다양한 분석/모델링 언어와 프레임 워크에 능숙한 역량 (PyTorch, Tensorflow, PySpark 등)
• 대형 언어 모델 (LLM)을 사용한 딥러닝 또는 자연어 처리에 대한 깊은 이해도

우대사항
• 데이터과학/공학 또는 통계학 관련 석사 학위
• Prompt Engineering, Fine-tuning 경험 있으신 분
• 생성형 AI 프로젝트 경험이 있으신 분
• 영어 회화 Skill 보유

혜택 및 복지
• 주 5일 유연근무제, 자율 책임근무
• 열린 문화, 배움을 장려하는 문화
• 외국어 및 기타 업무스킬관련 교육 무제한 지원
• 최신 맥북 지원
• 쿠팡 구매금액의 5% 캐시백 (최대 연간 400만원)
"""


@pytest.fixture
def coupang_company_summary():
    """쿠팡 회사 요약"""
    return """
쿠팡은 고객 감동 실현을 위해 존재하는 한국 최대 이커머스 기업입니다.
"쿠팡 없이 어떻게 살았을까?"를 목표로 고객의 쇼핑, 식사, 생활을 편리하게 만듭니다.
스타트업 문화를 유지하는 글로벌 대형 상장사로, 한국 시장에서 독보적인 명성을 쌓았습니다.
기업가 정신을 바탕으로 새로운 혁신과 이니셔티브를 추진하며, 커머스의 미래를 만들어갑니다.
CCP(Customer-Centric Planning)팀은 '고객의 소리'를 바탕으로 고객경험을 10배 이상 개선하는 미션을 수행합니다.
"""


@pytest.fixture(autouse=True)
def cleanup_sessions():
    """각 테스트 후 세션 정리"""
    yield
    session_states.clear()


# ==================== 헬퍼 함수 ====================


async def run_scenario(
    scenario: Dict,
    session_id: str,
    sample_resume: str,
    coupang_jd: str,
    coupang_company_summary: str = "",
) -> Dict:
    """단일 시나리오 실행"""

    # 상태 초기화
    state = get_session_state(
        session_id,
        job_description=coupang_jd,
        resume=sample_resume,
        company_summary=coupang_company_summary,
        user_resume=scenario.get("선택할이력서섹션", ""),
    )

    # 멀티스텝 처리
    is_multistep = scenario.get("멀티스텝", "X").strip().upper() == "O"
    input_messages = scenario.get("입력메시지", "")

    if is_multistep:
        # Step으로 분리된 메시지 처리
        steps = [s.strip() for s in input_messages.split("[Step") if s.strip()]
        for step_text in steps:
            # "[Step 1]" 형식에서 실제 메시지 추출
            if "]" in step_text:
                message = step_text.split("]", 1)[1].strip()
            else:
                message = step_text.strip()

            state.messages.append(HumanMessage(content=message))
            graph, state = await create_graph(state)
            result = await graph.ainvoke(state)
    else:
        # 단일 메시지 처리
        state.messages = [HumanMessage(content=input_messages)]
        graph, state = await create_graph(state)
        result = await graph.ainvoke(state)

    return result


def verify_keywords(response: str, expected_keywords: str) -> bool:
    """기대 키워드가 응답에 포함되어 있는지 확인"""
    if not expected_keywords or expected_keywords.strip() == "":
        return True

    keywords = [k.strip().lower() for k in expected_keywords.split(",") if k.strip()]
    response_lower = response.lower()

    # 키워드 중 최소 하나 이상 포함되어야 함
    matched = sum(1 for keyword in keywords if keyword in response_lower)
    return matched > 0


def verify_verification_point(response: str, verification_point: str) -> tuple[bool, str]:
    """검증 포인트 확인 (질문 형식)"""
    if not verification_point or verification_point.strip() == "":
        return True, "검증 포인트 없음"

    response_lower = response.lower()
    vp_lower = verification_point.lower()

    # 검증 포인트에서 핵심 키워드 추출 (한글, 영문)
    # 예: "경력 연수가 실제보다 과장되지 않았는가?" -> "경력", "연수", "과장"
    import re

    # 한글 키워드 추출
    korean_keywords = re.findall(r"[가-힣]+", vp_lower)
    # 영문 키워드 추출 (2글자 이상)
    english_keywords = re.findall(r"[a-z]{2,}", vp_lower)

    all_keywords = korean_keywords + english_keywords

    if not all_keywords:
        return True, "키워드 없음"

    # 키워드 매칭
    matched = [kw for kw in all_keywords if kw in response_lower]

    # 최소 30% 이상 매칭되면 통과
    match_rate = len(matched) / len(all_keywords) if all_keywords else 0

    return match_rate >= 0.3, f"매칭률: {match_rate:.1%} ({len(matched)}/{len(all_keywords)})"


def llm_judge(scenario: Dict, actual_response: str, model: str = "gpt-4.1") -> Dict:
    """
    LLM Judge를 사용하여 실제 응답을 평가합니다.

    Args:
        scenario: 테스트 시나리오 딕셔너리
        actual_response: 평가할 실제 응답
        model: 사용할 OpenAI 모델 (기본값: gpt-4o-mini)

    Returns:
        평가 결과 딕셔너리:
        {
            "score": float,  # 1-5 점수
            "reasoning": str,  # 평가 근거
            "verification_points": Dict,  # 검증 포인트별 평가
            "overall_feedback": str  # 전체 피드백
        }
    """
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        return {
            "score": 1.0,
            "reasoning": "OpenAI API key not found",
            "verification_points": {},
            "overall_feedback": "API 키가 설정되지 않아 평가를 수행할 수 없습니다.",
        }

    try:
        client = OpenAI(api_key=openai_api_key)

        # 평가 프롬프트 구성
        scenario_name = scenario.get("시나리오명", "")
        category = scenario.get("카테고리", "")
        priority = scenario.get("우선순위", "")
        input_message = scenario.get("입력메시지", "")
        selected_resume_section = scenario.get("선택할이력서섹션", "")
        expected_keywords = scenario.get("기대키워드", "")
        verification_points = [
            scenario.get("검증포인트1", ""),
            scenario.get("검증포인트2", ""),
            scenario.get("검증포인트3", ""),
        ]
        verification_points = [vp for vp in verification_points if vp and vp.strip()]

        judge_prompt = f"""당신은 이력서 개선 시스템의 응답 품질을 평가하는 전문가입니다.

## 시나리오 정보
- 시나리오명: {scenario_name}
- 카테고리: {category}
- 우선순위: {priority}
- 기대 키워드: {expected_keywords}
- 검증 포인트:
{chr(10).join(f"  {i+1}. {vp}" for i, vp in enumerate(verification_points))}

## 사용자 입력
### 사용자 질문:
{input_message}

### 선택한 이력서 섹션:
{selected_resume_section}

## 시스템의 실제 응답
{actual_response}

## 평가 기준
다음 항목들을 종합적으로 평가해주세요:
1. **정확성**: 사용자 질문을 정확히 이해하고 반영했는가?
2. **맥락 이해**: 선택한 이력서 섹션의 내용을 올바르게 이해하고 활용했는가?
3. **개선 품질**: 선택한 섹션을 사용자 질문에 맞게 효과적으로 개선했는가?
4. **완전성**: 기대 키워드가 적절히 포함되었는가?
5. **검증 포인트 충족**: 각 검증 포인트를 만족하는가?
6. **품질**: 응답의 구조, 명확성, 전문성이 적절한가?
7. **관련성**: 시나리오의 목적과 일치하는가?

## 점수 기준 (1-5점 척도)
- 5점: 모든 기준을 완벽하게 충족, 탁월한 품질
- 4점: 대부분의 기준을 잘 충족, 우수한 품질
- 3점: 기본적인 기준은 충족, 보통 품질
- 2점: 일부 기준 미충족, 개선 필요
- 1점: 대부분의 기준 미충족, 품질 불량

## 출력 형식
다음 JSON 형식으로 평가 결과를 제공해주세요:
{{
    "score": 1-5 사이의 점수 (정수),
    "reasoning": "점수에 대한 상세한 근거 설명",
    "verification_points": {{
        "검증포인트1": {{"met": true/false, "reason": "이유"}},
        "검증포인트2": {{"met": true/false, "reason": "이유"}},
        "검증포인트3": {{"met": true/false, "reason": "이유"}}
    }},
    "overall_feedback": "전체적인 피드백 및 개선 제안"
}}

JSON만 출력하고 다른 설명은 포함하지 마세요."""

        # gpt-4.1 모델 사용 (gpt-4.1, gpt-4.1-mini 등 시도)
        models_to_try = ["gpt-4.1", "gpt-4.1-mini", "gpt-4o-mini"]
        response = None
        last_error = None

        for model_name in models_to_try:
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "당신은 이력서 개선 시스템의 응답 품질을 평가하는 전문가입니다. 항상 JSON 형식으로만 응답합니다.",
                        },
                        {"role": "user", "content": judge_prompt},
                    ],
                    temperature=0.3,
                    max_tokens=2000,
                    response_format={"type": "json_object"},
                )
                print(f"  LLM Judge 모델 사용: {model_name}")
                break
            except Exception as e:
                last_error = e
                continue

        if response is None:
            raise Exception(f"모든 모델 시도 실패. 마지막 오류: {str(last_error)}")

        result_text = response.choices[0].message.content.strip()

        # JSON 파싱
        try:
            result = json.loads(result_text)
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 텍스트에서 점수 추출 시도
            import re

            score_match = re.search(r'"score"\s*:\s*(\d+)', result_text)
            score = int(score_match.group(1)) if score_match else 3

            # 점수를 1-5 범위로 제한
            score = max(1, min(5, score))

            return {
                "score": float(score),
                "reasoning": result_text[:500] if len(result_text) > 500 else result_text,
                "verification_points": {},
                "overall_feedback": result_text,
            }

        # 결과 정규화 및 점수 범위 제한 (1-5)
        raw_score = result.get("score", 3)
        # 점수가 1-5 범위를 벗어나면 조정
        if raw_score > 5:
            # 100점 척도로 들어온 경우 5점 척도로 변환
            normalized_score = max(1, min(5, round(raw_score / 20)))
        else:
            normalized_score = max(1, min(5, int(raw_score)))

        return {
            "score": float(normalized_score),
            "reasoning": result.get("reasoning", ""),
            "verification_points": result.get("verification_points", {}),
            "overall_feedback": result.get("overall_feedback", ""),
        }

    except Exception as e:
        return {
            "score": 1.0,
            "reasoning": f"평가 중 오류 발생: {str(e)}",
            "verification_points": {},
            "overall_feedback": f"LLM Judge 평가 실패: {str(e)}",
        }


def save_test_results_to_csv(test_results: List[Dict], base_csv_path: str = None, output_dir: str = None) -> str:
    """테스트 결과를 기존 CSV 형식에 실제응답과 LLM Judge 결과를 추가하여 저장"""
    if output_dir is None:
        output_dir = project_root / "backend" / "tests" / "results"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    # 기본 CSV 파일 경로 (test_scenarios_full.csv)
    if base_csv_path is None:
        base_csv_path = project_root / "test_scenarios_full.csv"
    else:
        base_csv_path = Path(base_csv_path)

    # 기본 CSV 파일 읽기
    base_rows = {}
    base_fieldnames = []

    if base_csv_path.exists():
        with open(base_csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            base_fieldnames = reader.fieldnames
            for row in reader:
                scenario_id = row.get("ID", "")
                base_rows[scenario_id] = row
    else:
        # 기본 CSV가 없으면 기본 필드명 사용
        base_fieldnames = [
            "ID",
            "시나리오명",
            "카테고리",
            "난이도",
            "우선순위",
            "예상소요시간",
            "멀티스텝",
            "입력메시지",
            "선택할이력서섹션",
            "기대키워드",
            "검증포인트1",
            "검증포인트2",
            "검증포인트3",
            "비고",
        ]

    # 테스트 결과를 ID로 매핑
    test_results_by_id = {}
    for result in test_results:
        scenario_id = result.get("id", "")
        test_results_by_id[scenario_id] = result

    # 새로운 필드명: 기존 필드 + 실제응답 + LLM Judge 결과
    new_fieldnames = list(base_fieldnames) + ["실제응답", "LLM_Judge_점수", "LLM_Judge_근거"]

    # 타임스탬프를 포함한 파일명 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = output_dir / f"test_scenarios_with_results_{timestamp}.csv"

    # CSV 파일 작성
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=new_fieldnames)
        writer.writeheader()

        # 기존 CSV의 모든 행에 대해 처리
        for scenario_id, base_row in base_rows.items():
            new_row = base_row.copy()

            # 테스트 결과가 있으면 추가
            if scenario_id in test_results_by_id:
                test_result = test_results_by_id[scenario_id]
                new_row["실제응답"] = test_result.get("response", "")
                new_row["LLM_Judge_점수"] = test_result.get("llm_judge_score", "")
                new_row["LLM_Judge_근거"] = test_result.get("llm_judge_reasoning", "")
            else:
                new_row["실제응답"] = ""
                new_row["LLM_Judge_점수"] = ""
                new_row["LLM_Judge_근거"] = ""

            writer.writerow(new_row)

    return str(csv_path)


# ==================== 필수 시나리오 테스트 ====================


@pytest.mark.asyncio
class TestMandatoryScenarios:
    """우선순위: 필수 - 반드시 통과해야 하는 핵심 시나리오"""

    async def test_scenario_01_경력_갭_메우기(self, sample_resume, coupang_jd):
        """시나리오 1: 경력 갭 메우기 - 기본 개선"""
        scenario = {
            "입력메시지": "쿠팡 Data Scientist 5년 경력 요구사항에 맞춰 경험을 강조해줘",
            "선택할이력서섹션": """오케스트로 | ML Engineer (2023.08 ~ Present)
• LLM 시스템 추론 성능 최적화
  - vLLM 프레임워크를 활용하여 Batch Processing 및 KV Cache 최적화 구현
  - Throughput 기준 2.5배, Latency 기준 1.9배 성능 개선""",
            "기대키워드": "프로덕션, 배포, 최적화",
            "멀티스텝": "X",
        }

        session_id = "scenario_01"
        result = await run_scenario(scenario, session_id, sample_resume, coupang_jd)
        response = result["messages"][-1].content

        # 검증 1: 응답이 존재하는가?
        assert len(response) > 0, "응답이 비어있습니다"

        # 검증 2: 기대 키워드 포함 여부
        assert verify_keywords(
            response, scenario["기대키워드"]
        ), f"기대 키워드가 포함되지 않았습니다: {scenario['기대키워드']}"

        # 검증 3: 경력 연수가 과장되지 않았는가? (2023.08 ~ Present = 약 2년)
        assert "5년" not in response or "5년 이상" not in response, "경력 연수가 실제보다 과장되었습니다"

        # 검증 4: 구체적인 수치 포함
        import re

        numbers = re.findall(r"\d+\.?\d*[배|배치|%|개|번|초|분|시간]", response)
        assert len(numbers) >= 1, "구체적인 수치가 포함되지 않았습니다"

        end_session(session_id)

    async def test_scenario_02_쿠팡_문화_fit(self, sample_resume, coupang_jd):
        """시나리오 2: 쿠팡 문화 Fit - 고객 중심 프레이밍"""
        scenario = {
            "입력메시지": "쿠팡의 '고객 중심' 문화에 맞춰 경험을 프레이밍해줘",
            "선택할이력서섹션": """퍼블리 | QA 홈페이지 챗봇 개발 (2023.04 ~ 2023.08)
• RAG 기반 FAQ 챗봇 시스템 설계 및 구현
• OpenAI API를 활용한 자연어 처리
• Pinecone을 활용한 벡터 임베딩 및 유사도 검색""",
            "기대키워드": "고객, 사용자, 경험, 문제, 해결",
            "멀티스텝": "X",
        }

        session_id = "scenario_02"
        result = await run_scenario(scenario, session_id, sample_resume, coupang_jd)
        response = result["messages"][-1].content

        assert len(response) > 0
        assert verify_keywords(
            response, scenario["기대키워드"]
        ), f"고객 중심 키워드가 포함되지 않았습니다: {scenario['기대키워드']}"

        # 기술 중심 → 고객 가치 중심으로 변경 확인
        customer_keywords = ["고객", "사용자", "문제", "해결", "개선", "경험"]
        matched = sum(1 for kw in customer_keywords if kw in response)
        assert matched >= 2, f"고객 중심 키워드가 충분하지 않습니다 (매칭: {matched}/6)"

        end_session(session_id)

    async def test_scenario_03_llm_poc_강조(self, sample_resume, coupang_jd):
        """시나리오 3: LLM POC 강조 - 기술 맞춤"""
        scenario = {
            "입력메시지": "쿠팡 JD의 'LLM 모델 구축, POC 수행 및 최적화' 요구사항에 맞춰 개선해줘",
            "선택할이력서섹션": """• 한국행정연구원 보고서 목차별 요약 POC
  - 행정연구원 보고서 자동 요약 시스템 설계
  - LLM-as-a-Judge 기법을 통한 요약 성능 평가""",
            "기대키워드": "llm, poc, 최적화, 프로덕션, 배포, 모델",
            "멀티스텝": "X",
        }

        session_id = "scenario_03"
        result = await run_scenario(scenario, session_id, sample_resume, coupang_jd)
        response = result["messages"][-1].content.lower()

        assert len(response) > 0

        # JD 키워드가 3개 이상 포함되었는가?
        key_requirements = ["llm", "poc", "최적화", "프로덕션", "배포", "모델"]
        matched = sum(1 for keyword in key_requirements if keyword.lower() in response)
        assert matched >= 3, f"JD 키워드가 충분하지 않습니다 (매칭: {matched}/6, 최소 3개 필요)"

        end_session(session_id)

    async def test_scenario_10_멀티턴_점진적_개선(self, sample_resume, coupang_jd):
        """시나리오 10: 멀티턴 점진적 개선 - 대화 품질"""
        scenario = {
            "입력메시지": """[Step 1] 이 경험을 쿠팡 Data Scientist에 맞게 개선해줘
[Step 2] 생성형 AI 측면을 더 강조해줘
[Step 3] 비즈니스 임팩트를 수치로 추가해줘
[Step 4] 고객 중심 관점도 추가해줘""",
            "선택할이력서섹션": """퍼블리 | QA 홈페이지 챗봇 개발 (2023.04 ~ 2023.08)
• RAG 기반 FAQ 챗봇 시스템 설계 및 구현
• OpenAI API를 활용한 자연어 처리
• Pinecone을 활용한 벡터 임베딩 및 유사도 검색""",
            "기대키워드": "점진적 개선, 맥락 유지, 통합",
            "멀티스텝": "O",
        }

        session_id = "scenario_10"
        result = await run_scenario(scenario, session_id, sample_resume, coupang_jd)
        response = result["messages"][-1].content

        assert len(response) > 0

        # 대화 맥락이 유지되는가? (마지막 응답에 모든 요청이 반영되었는지)
        requirements = ["생성형 ai", "ai", "수치", "숫자", "고객"]
        matched = sum(1 for req in requirements if req in response.lower())
        assert matched >= 2, f"멀티턴 요청이 충분히 반영되지 않았습니다 (매칭: {matched}/5)"

        end_session(session_id)

    async def test_scenario_16_긴_입력(self, sample_resume, coupang_jd):
        """시나리오 16: 에지케이스 - 긴 입력 처리"""
        scenario = {
            "입력메시지": "쿠팡 JD에 맞춰 개선해줘",
            "선택할이력서섹션": sample_resume,  # 전체 이력서
            "기대키워드": "통합 개선, 일관성",
            "멀티스텝": "X",
        }

        session_id = "scenario_16"
        start_time = time.time()

        try:
            result = await run_scenario(scenario, session_id, sample_resume, coupang_jd)
            elapsed_time = time.time() - start_time
            response = result["messages"][-1].content

            # 긴 입력을 잘 처리했는가?
            assert len(response) > 0, "응답이 비어있습니다"

            # 응답 시간이 합리적인가? (60초 이내)
            assert elapsed_time < 60.0, f"응답 시간이 너무 깁니다: {elapsed_time:.1f}초 (최대 60초)"

        except Exception as e:
            pytest.fail(f"긴 입력 처리 실패: {str(e)}")
        finally:
            end_session(session_id)

    async def test_scenario_19_복합_요청(self, sample_resume, coupang_jd):
        """시나리오 19: 복합 요청 - 여러 요구사항 동시 처리"""
        scenario = {
            "입력메시지": "쿠팡 Data Scientist JD에 맞춰 1) 생성형 AI 경험 강조, 2) 고객 중심 프레이밍, 3) 수치적 성과 추가해서 개선해줘",
            "선택할이력서섹션": """• AI 면접관 챗봇 서비스 구축
  - RAG 기반 면접 질의응답 시스템 설계 및 구현
  - ChromaDB를 활용한 벡터 데이터베이스 구축""",
            "기대키워드": "생성형 AI, 고객, 수치",
            "멀티스텝": "X",
        }

        session_id = "scenario_19"
        result = await run_scenario(scenario, session_id, sample_resume, coupang_jd)
        response = result["messages"][-1].content.lower()

        assert len(response) > 0

        # 모든 요구사항이 반영되었는가?
        req1 = any(kw in response for kw in ["생성형 ai", "generative ai", "llm", "rag"])
        req2 = any(kw in response for kw in ["고객", "사용자", "user", "customer"])
        req3 = any(char.isdigit() for char in response)  # 수치 포함

        assert req1, "생성형 AI 경험이 강조되지 않았습니다"
        assert req2, "고객 중심 프레이밍이 누락되었습니다"
        assert req3, "수치적 성과가 추가되지 않았습니다"

        end_session(session_id)

    async def test_scenario_20_관련_없는_경험(self, sample_resume, coupang_jd):
        """시나리오 20: 부정 테스트 - 관련 없는 경험 처리"""
        scenario = {
            "입력메시지": "쿠팡 Data Scientist에 맞춰 개선해줘",
            "선택할이력서섹션": """스타벅스 바리스타 (2020 ~ 2021)
• 커피 제조 및 고객 서비스
• 재고 관리 및 매장 운영""",
            "기대키워드": "관련성 낮음, 전이 가능 스킬, 정직한 피드백",
            "멀티스텝": "X",
        }

        session_id = "scenario_20"
        result = await run_scenario(scenario, session_id, sample_resume, coupang_jd)
        response = result["messages"][-1].content.lower()

        assert len(response) > 0

        # 억지로 기술 경험과 연결하지 않았는가?
        tech_keywords = ["machine learning", "ml", "python", "model", "algorithm", "llm"]
        forced_connection = sum(1 for kw in tech_keywords if kw in response)

        # 기술 키워드가 과도하게 많으면 억지 연결로 판단
        assert (
            forced_connection < 3
        ), f"관련 없는 경험을 억지로 기술 경험과 연결했습니다 (기술 키워드: {forced_connection}개)"

        # 전이 가능한 소프트 스킬 강조 확인 (고객 서비스, 협업 등)
        soft_skills = ["고객", "서비스", "협업", "소통", "관리", "customer", "service", "communication"]
        soft_skill_mention = sum(1 for skill in soft_skills if skill in response)

        assert soft_skill_mention >= 1, "전이 가능한 스킬이 강조되지 않았습니다"

        end_session(session_id)


# ==================== 권장 시나리오 테스트 ====================


@pytest.mark.asyncio
class TestRecommendedScenarios:
    """우선순위: 권장 - 시스템 품질 향상을 위한 시나리오"""

    async def test_scenario_04_멀티_에이전트_강조(self, sample_resume, coupang_jd):
        """시나리오 4: 멀티 에이전트 경험 강조"""
        scenario = {
            "입력메시지": "생성형 AI를 활용한 최첨단 솔루션 구현' 요구사항에 맞춰 멀티 에이전트 경험을 개선해줘",
            "선택할이력서섹션": """• AI 면접관 챗봇 서비스 구축
  - RAG 기반 면접 질의응답 시스템 설계 및 구현
  - ChromaDB를 활용한 벡터 데이터베이스 구축
  - LangChain, LangGraph를 활용한 멀티 에이전트 시스템 개발""",
            "기대키워드": "생성형 AI, 솔루션, 최첨단",
            "멀티스텝": "X",
        }

        session_id = "scenario_04"
        result = await run_scenario(scenario, session_id, sample_resume, coupang_jd)
        response = result["messages"][-1].content.lower()

        assert len(response) > 0
        assert verify_keywords(response, scenario["기대키워드"])

        # 생성형 AI 활용 측면이 강조되었는가?
        gen_ai_keywords = ["생성형", "generative", "llm", "rag", "agent"]
        matched = sum(1 for kw in gen_ai_keywords if kw in response)
        assert matched >= 2, f"생성형 AI 키워드가 충분하지 않습니다 (매칭: {matched}/5)"

        end_session(session_id)

    async def test_scenario_05_python_프레임워크_역량(self, sample_resume, coupang_jd):
        """시나리오 5: Python & ML 프레임워크 역량 강조"""
        scenario = {
            "입력메시지": "Python과 ML 프레임워크(PyTorch 등) 역량을 강조해서 개선해줘",
            "선택할이력서섹션": """Skills
• Languages: Python, SQL
• ML/AI: PyTorch, LangChain, LangGraph, OpenAI API, RAG""",
            "기대키워드": "PyTorch, Python, 프레임워크",
            "멀티스텝": "X",
        }

        session_id = "scenario_05"
        result = await run_scenario(scenario, session_id, sample_resume, coupang_jd)
        response = result["messages"][-1].content

        assert len(response) > 0
        assert verify_keywords(response, scenario["기대키워드"])

        # 단순 나열 → 실제 사용 경험으로 변경되었는가?
        experience_keywords = ["구현", "개발", "활용", "사용", "프로젝트", "경험", "implement", "develop"]
        has_experience = any(kw in response.lower() for kw in experience_keywords)
        assert has_experience, "기술 스택이 단순 나열에 그치고 실제 사용 경험이 드러나지 않습니다"

        end_session(session_id)

    async def test_scenario_08_성과_지표_극대화(self, sample_resume, coupang_jd):
        """시나리오 8: 성과 지표 극대화 - 임팩트 강화"""
        scenario = {
            "입력메시지": "비즈니스 임팩트와 수치적 성과를 최대한 강조해서 개선해줘",
            "선택할이력서섹션": """• AI 면접관 챗봇 서비스 구축
  - RAG 기반 면접 질의응답 시스템 설계 및 구현
  - ChromaDB를 활용한 벡터 데이터베이스 구축
  - LangChain, LangGraph를 활용한 멀티 에이전트 시스템 개발""",
            "기대키워드": "시간 절감, 효율성, 정확도, 응답 시간",
            "멀티스텝": "X",
        }

        session_id = "scenario_08"
        result = await run_scenario(scenario, session_id, sample_resume, coupang_jd)
        response = result["messages"][-1].content

        assert len(response) > 0

        # 수치가 구체적으로 포함되었는가?
        import re

        numbers = re.findall(r"\d+\.?\d*\s*[%배배치개번초분시간명]", response)
        assert len(numbers) >= 2, f"수치적 성과가 충분하지 않습니다 (발견: {len(numbers)}개, 최소 2개 필요)"

        # 비즈니스 가치 키워드 포함 확인
        business_keywords = ["절감", "향상", "개선", "증가", "효율", "생산성", "임팩트"]
        has_business_value = any(kw in response for kw in business_keywords)
        assert has_business_value, "비즈니스 가치가 명확하지 않습니다"

        end_session(session_id)

    async def test_scenario_14_문제_해결_스토리텔링(self, sample_resume, coupang_jd):
        """시나리오 14: 문제 해결 스토리텔링 - STAR 형식"""
        scenario = {
            "입력메시지": "LLM 최적화 과정에서 직면한 문제와 해결 과정을 스토리로 풀어서 개선해줘",
            "선택할이력서섹션": """• LLM 시스템 추론 성능 최적화
  - vLLM 프레임워크를 활용하여 Batch Processing 및 KV Cache 최적화 구현
  - Throughput 기준 2.5배, Latency 기준 1.9배 성능 개선""",
            "기대키워드": "문제, 해결, 결과, STAR",
            "멀티스텝": "X",
        }

        session_id = "scenario_14"
        result = await run_scenario(scenario, session_id, sample_resume, coupang_jd)
        response = result["messages"][-1].content.lower()

        assert len(response) > 0

        # STAR 구조 확인: Situation, Task, Action, Result
        star_keywords = {
            "situation": ["문제", "상황", "필요", "요구", "challenge", "problem", "issue"],
            "task": ["목표", "과제", "미션", "goal", "objective", "target"],
            "action": ["구현", "적용", "사용", "개선", "implement", "apply", "use", "improve"],
            "result": ["결과", "성과", "달성", "향상", "result", "achieve", "improve", "배"],
        }

        star_matched = 0
        for category, keywords in star_keywords.items():
            if any(kw in response for kw in keywords):
                star_matched += 1

        # 최소 3개 영역이 포함되어야 함 (S, A, R 필수)
        assert star_matched >= 3, f"STAR 구조가 충분하지 않습니다 (매칭: {star_matched}/4 영역)"

        end_session(session_id)

    async def test_scenario_17_애매한_요청(self, sample_resume, coupang_jd):
        """시나리오 17: 에지케이스 - 애매한 요청 처리"""
        scenario = {
            "입력메시지": "더 좋게 해줘",
            "선택할이력서섹션": """• LLM 시스템 추론 성능 최적화
  - vLLM 프레임워크를 활용하여 Batch Processing 및 KV Cache 최적화 구현""",
            "기대키워드": "자동 해석, 합리적 개선",
            "멀티스텝": "X",
        }

        session_id = "scenario_17"
        result = await run_scenario(scenario, session_id, sample_resume, coupang_jd)
        response = result["messages"][-1].content

        assert len(response) > 0, "애매한 요청에도 응답해야 합니다"

        # 애매한 요청을 JD 컨텍스트를 활용하여 해석했는가?
        jd_keywords = ["data scientist", "llm", "python", "pytorch", "최적화", "프로덕션"]
        matched = sum(1 for kw in jd_keywords if kw.lower() in response.lower())

        assert matched >= 1, "JD 컨텍스트를 활용하지 않았습니다"

        # 합리적인 개선이 이루어졌는가? (단순 반복이 아닌 실질적 개선)
        assert len(response) > len(scenario["선택할이력서섹션"]) * 0.8, "개선이 너무 단순하거나 내용이 누락되었습니다"

        end_session(session_id)

    async def test_scenario_18_짧은_입력(self, sample_resume, coupang_jd):
        """시나리오 18: 에지케이스 - 짧은 입력 확장"""
        scenario = {
            "입력메시지": "생성형 AI 경험을 강조해줘",
            "선택할이력서섹션": "• LLM 최적화",
            "기대키워드": "구체화, 확장, 사실 기반",
            "멀티스텝": "X",
        }

        session_id = "scenario_18"
        result = await run_scenario(scenario, session_id, sample_resume, coupang_jd)
        response = result["messages"][-1].content

        assert len(response) > 0

        # 짧은 입력을 잘 확장했는가?
        assert len(response) > len(scenario["선택할이력서섹션"]) * 3, "짧은 입력이 충분히 확장되지 않았습니다"

        # 사실 기반인가? (전체 이력서 컨텍스트 활용)
        resume_keywords = ["vllm", "pytorch", "langgraph", "fastapi", "오케스트로"]
        fact_based = any(kw in response.lower() for kw in resume_keywords)

        assert fact_based, "사실 기반이 아닌 추측성 내용이 포함되었습니다"

        end_session(session_id)

    async def test_scenario_21_빠른_응답(self, sample_resume, coupang_jd):
        """시나리오 21: 성능 테스트 - 빠른 응답"""
        scenario = {
            "입력메시지": "bullet point 형식으로 정리해줘",
            "선택할이력서섹션": "LLM 시스템 추론 성능 최적화를 했고, vLLM을 사용해서 2.5배 성능 개선했습니다.",
            "기대키워드": "형식 변환, 빠른 응답",
            "멀티스텝": "X",
        }

        session_id = "scenario_21"
        start_time = time.time()

        result = await run_scenario(scenario, session_id, sample_resume, coupang_jd)
        elapsed_time = time.time() - start_time
        response = result["messages"][-1].content

        assert len(response) > 0

        # 응답 시간이 15초 이내인가?
        assert elapsed_time < 15.0, f"응답 시간이 너무 깁니다: {elapsed_time:.1f}초 (최대 15초)"

        # Bullet point 형식 확인
        bullet_markers = ["•", "-", "*", "▪", "◦"]
        has_bullets = any(marker in response for marker in bullet_markers)
        assert has_bullets, "Bullet point 형식으로 변환되지 않았습니다"

        end_session(session_id)


# ==================== 선택 시나리오 테스트 ====================


@pytest.mark.asyncio
class TestOptionalScenarios:
    """우선순위: 선택 - 추가 개선을 위한 시나리오"""

    async def test_scenario_13_크로스_펑셔널_협업(self, sample_resume, coupang_jd):
        """시나리오 13: 크로스 펑셔널 협업 강조"""
        scenario = {
            "입력메시지": "프로덕트 매니저, 디자이너 등 다른 팀과 협업한 경험을 강조해줘",
            "선택할이력서섹션": """• AI 면접관 챗봇 서비스 구축
  - RAG 기반 면접 질의응답 시스템 설계 및 구현
  - ChromaDB를 활용한 벡터 데이터베이스 구축
  - LangChain, LangGraph를 활용한 멀티 에이전트 시스템 개발""",
            "기대키워드": "PM, 디자이너, 협업, 소통",
            "멀티스텝": "X",
        }

        session_id = "scenario_13"
        result = await run_scenario(scenario, session_id, sample_resume, coupang_jd)
        response = result["messages"][-1].content.lower()

        assert len(response) > 0

        # 다양한 이해관계자와의 소통이 드러나는가?
        collaboration_keywords = [
            "협업",
            "소통",
            "pm",
            "디자이너",
            "팀",
            "조율",
            "함께",
            "collaboration",
            "communication",
        ]
        matched = sum(1 for kw in collaboration_keywords if kw in response)

        assert matched >= 1, f"협업 관련 키워드가 충분하지 않습니다 (매칭: {matched}/9)"

        end_session(session_id)

    async def test_scenario_22_한영_혼용(self, sample_resume, coupang_jd):
        """시나리오 22: 한영 혼용 처리"""
        scenario = {
            "입력메시지": "Coupang의 LLM POC requirement에 맞춰 개선해주세요",
            "선택할이력서섹션": """• Developed LLM 기반 챗봇
• PyTorch를 활용한 model optimization""",
            "기대키워드": "한영 혼용, 일관성",
            "멀티스텝": "X",
        }

        session_id = "scenario_22"
        result = await run_scenario(scenario, session_id, sample_resume, coupang_jd)
        response = result["messages"][-1].content

        assert len(response) > 0

        # 한영 혼용을 자연스럽게 처리했는가?
        # (한글 문장 내에 영문 기술 용어는 허용)
        import re

        # 한글과 영어가 모두 포함되어 있는지 확인
        has_korean = bool(re.search(r"[가-힣]", response))
        has_english = bool(re.search(r"[a-zA-Z]", response))

        assert has_korean and has_english, "한영 혼용이 적절히 처리되지 않았습니다"

        end_session(session_id)

    async def test_scenario_23_회사_문화_깊이_파기(self, sample_resume, coupang_jd):
        """시나리오 23: 회사 문화 깊이 파기"""
        scenario = {
            "입력메시지": '쿠팡의 "고객 없이는 우리도 없다" 원칙에 맞춰 개선해줘',
            "선택할이력서섹션": """• LLM 시스템 추론 성능 최적화
  - Throughput 기준 2.5배, Latency 기준 1.9배 성능 개선""",
            "기대키워드": "고객 경험, 임팩트, 쿠팡 가치",
            "멀티스텝": "X",
        }

        session_id = "scenario_23"
        result = await run_scenario(scenario, session_id, sample_resume, coupang_jd)
        response = result["messages"][-1].content

        assert len(response) > 0

        # 기술 → 고객 가치로 전환되었는가?
        customer_value_keywords = ["고객", "사용자", "경험", "만족", "가치", "customer", "user", "experience"]
        matched = sum(1 for kw in customer_value_keywords if kw.lower() in response.lower())

        assert matched >= 1, f"고객 가치 전환이 이루어지지 않았습니다 (매칭: {matched}/8)"

        end_session(session_id)

    async def test_scenario_24_트렌드_반영(self, sample_resume, coupang_jd):
        """시나리오 24: 최신 LLM 트렌드 반영"""
        scenario = {
            "입력메시지": "RAG, Fine-tuning, Prompt Engineering 등 최신 LLM 트렌드를 반영해서 개선해줘",
            "선택할이력서섹션": """• AI 면접관 챗봇 서비스 구축
  - RAG 기반 면접 질의응답 시스템 설계 및 구현""",
            "기대키워드": "RAG, Fine-tuning, Prompt Engineering",
            "멀티스텝": "X",
        }

        session_id = "scenario_24"
        result = await run_scenario(scenario, session_id, sample_resume, coupang_jd)
        response = result["messages"][-1].content.lower()

        assert len(response) > 0

        # 최신 AI 트렌드가 반영되었는가?
        trend_keywords = ["rag", "fine-tuning", "prompt engineering", "llm", "embedding", "retrieval"]
        matched = sum(1 for kw in trend_keywords if kw in response)

        assert matched >= 2, f"최신 LLM 트렌드가 충분히 반영되지 않았습니다 (매칭: {matched}/6)"

        end_session(session_id)


# ==================== 통합 벤치마크 ====================


@pytest.mark.asyncio
class TestFullBenchmark:
    """전체 시나리오 실행 및 통계"""

    async def test_all_scenarios_benchmark(self, test_scenarios, sample_resume, coupang_jd, coupang_company_summary):
        """모든 시나리오 벤치마크 테스트"""
        results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "by_priority": {
                "필수": {"total": 0, "passed": 0},
                "권장": {"total": 0, "passed": 0},
                "선택": {"total": 0, "passed": 0},
            },
            "by_category": {},
            "total_time": 0,
            "failures": [],
        }

        # CSV 저장을 위한 상세 결과 리스트
        csv_results = []

        for i, scenario in enumerate(test_scenarios):
            session_id = f"benchmark_{i}"
            priority = scenario.get("우선순위", "선택")
            category = scenario.get("카테고리", "기타")
            scenario_id = scenario.get("ID", f"SCENARIO_{i}")
            scenario_name = scenario.get("시나리오명", "")
            multistep = scenario.get("멀티스텝", "X")
            input_message = scenario.get("입력메시지", "")
            expected_keywords = scenario.get("기대키워드", "")

            results["total"] += 1
            results["by_priority"][priority]["total"] += 1

            if category not in results["by_category"]:
                results["by_category"][category] = {"total": 0, "passed": 0}
            results["by_category"][category]["total"] += 1

            # CSV 결과 초기화
            csv_result = {
                "id": scenario_id,
                "name": scenario_name,
                "category": category,
                "priority": priority,
                "multistep": multistep,
                "status": "FAIL",
                "elapsed_time": 0,
                "failure_reason": "",
                "response_length": 0,
                "keyword_match": False,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "input_message": input_message,
                "expected_keywords": expected_keywords,
                "response": "",
                "llm_judge_score": 1.0,
                "llm_judge_reasoning": "",
                "llm_judge_feedback": "",
                "llm_judge_verification_points": "",
            }

            try:
                start_time = time.time()
                result = await run_scenario(scenario, session_id, sample_resume, coupang_jd, coupang_company_summary)
                elapsed = time.time() - start_time

                results["total_time"] += elapsed
                csv_result["elapsed_time"] = f"{elapsed:.2f}"

                response = result["messages"][-1].content
                csv_result["response_length"] = len(response)
                csv_result["response"] = response  # 실제 응답 내용 저장

                # 기본 검증: 응답 존재 & 키워드 포함
                keyword_match = verify_keywords(response, expected_keywords)
                csv_result["keyword_match"] = keyword_match

                # LLM Judge 평가 수행
                print(f"\n[{scenario_id}] LLM Judge 평가 중...")
                judge_result = llm_judge(scenario, response)
                csv_result["llm_judge_score"] = judge_result["score"]
                csv_result["llm_judge_reasoning"] = judge_result["reasoning"]
                csv_result["llm_judge_feedback"] = judge_result["overall_feedback"]
                csv_result["llm_judge_verification_points"] = json.dumps(
                    judge_result["verification_points"], ensure_ascii=False
                )
                print(f"[{scenario_id}] LLM Judge 점수: {judge_result['score']:.1f}/5")

                if len(response) > 0 and keyword_match:
                    results["passed"] += 1
                    results["by_priority"][priority]["passed"] += 1
                    results["by_category"][category]["passed"] += 1
                    csv_result["status"] = "PASS"
                else:
                    results["failed"] += 1
                    failure_reason = "Response empty" if len(response) == 0 else "Missing keywords"
                    results["failures"].append(
                        {
                            "id": scenario_id,
                            "name": scenario_name,
                            "reason": failure_reason,
                        }
                    )
                    csv_result["status"] = "FAIL"
                    csv_result["failure_reason"] = failure_reason

                print(f"\n[{scenario_id}] {scenario_name}: {elapsed:.2f}s - {csv_result['status']}")

            except Exception as e:
                results["failed"] += 1
                failure_reason = str(e)
                results["failures"].append(
                    {
                        "id": scenario_id,
                        "name": scenario_name,
                        "reason": failure_reason,
                    }
                )
                csv_result["status"] = "FAIL"
                csv_result["failure_reason"] = failure_reason
                # 예외 발생 시에도 응답이 있다면 저장
                if "response" not in csv_result or not csv_result["response"]:
                    csv_result["response"] = f"Error: {failure_reason}"
                # 예외 발생 시 LLM Judge는 수행하지 않음
                csv_result["llm_judge_score"] = 1.0
                csv_result["llm_judge_reasoning"] = f"테스트 실패로 인해 평가 불가: {failure_reason}"
                csv_result["llm_judge_feedback"] = ""
                csv_result["llm_judge_verification_points"] = ""
                print(f"\n[{scenario_id}] {scenario_name}: FAIL - {failure_reason}")

            finally:
                csv_results.append(csv_result)
                end_session(session_id)

        # 결과 출력
        print(f"\n{'='*70}")
        print(f"전체 벤치마크 결과")
        print(f"{'='*70}")
        print(f"총 시나리오: {results['total']}")
        print(f"통과: {results['passed']} ({results['passed']/results['total']*100:.1f}%)")
        print(f"실패: {results['failed']} ({results['failed']/results['total']*100:.1f}%)")
        print(f"총 소요 시간: {results['total_time']:.1f}초")
        print(f"평균 소요 시간: {results['total_time']/results['total']:.1f}초")

        print(f"\n우선순위별 결과:")
        for priority, stats in results["by_priority"].items():
            if stats["total"] > 0:
                rate = stats["passed"] / stats["total"] * 100
                print(f"  {priority}: {stats['passed']}/{stats['total']} ({rate:.1f}%)")

        print(f"\n카테고리별 결과:")
        for category, stats in results["by_category"].items():
            if stats["total"] > 0:
                rate = stats["passed"] / stats["total"] * 100
                print(f"  {category}: {stats['passed']}/{stats['total']} ({rate:.1f}%)")

        if results["failures"]:
            print(f"\n실패한 시나리오:")
            for failure in results["failures"][:5]:  # 최대 5개만 표시
                print(f"  [{failure['id']}] {failure['name']}: {failure['reason']}")

        print(f"{'='*70}\n")

        # CSV 파일로 결과 저장 (기존 test_scenarios_full.csv 형식에 실제응답과 LLM Judge 결과 추가)
        base_csv_path = project_root / "test_scenarios_full.csv"
        csv_path = save_test_results_to_csv(csv_results, base_csv_path=str(base_csv_path))
        print(f"\n테스트 결과가 CSV 파일로 저장되었습니다: {csv_path}\n")
        print(f"기존 CSV 형식(test_scenarios_full.csv)에 실제응답과 LLM Judge 결과가 추가되었습니다.\n")

        # 필수 시나리오는 90% 이상 통과해야 함
        if results["by_priority"]["필수"]["total"] > 0:
            mandatory_pass_rate = results["by_priority"]["필수"]["passed"] / results["by_priority"]["필수"]["total"]
            assert mandatory_pass_rate >= 0.9, f"필수 시나리오 통과율이 90% 미만입니다: {mandatory_pass_rate:.1%}"

        # 전체 시나리오는 70% 이상 통과해야 함
        overall_pass_rate = results["passed"] / results["total"]
        assert overall_pass_rate >= 0.7, f"전체 시나리오 통과율이 70% 미만입니다: {overall_pass_rate:.1%}"


if __name__ == "__main__":
    # 직접 실행 시 필수 시나리오만 실행
    print("필수 시나리오 테스트 실행...")
    pytest.main([__file__, "-v", "-k", "TestMandatoryScenarios"])
