"""
Pytest 설정 파일
공통 fixture 및 설정을 정의합니다.
"""

import pytest
import sys
import os
from pathlib import Path
from datetime import datetime
import csv

# 프로젝트 루트를 Python path에 추가
# conftest.py는 backend/tests/에 있으므로, 프로젝트 루트는 2단계 위
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # backend 디렉토리

# 테스트 결과 수집을 위한 전역 변수
_test_results = []


def pytest_configure(config):
    """pytest 실행 전 설정"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )


@pytest.fixture(scope="session")
def event_loop():
    """전체 테스트 세션에 대한 이벤트 루프 제공"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


def pytest_runtest_makereport(item, call):
    """각 테스트의 결과를 수집"""
    if "test_scenario" in item.name:
        result = {
            'test_name': item.name,
            'status': 'UNKNOWN',
            'duration': 0,
            'error': '',
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        if call.when == "call":
            if call.excinfo is None:
                result['status'] = 'PASS'
            else:
                result['status'] = 'FAIL'
                result['error'] = str(call.excinfo.value)
            
            if hasattr(call, 'duration'):
                result['duration'] = call.duration
        
        _test_results.append(result)


def pytest_sessionfinish(session, exitstatus):
    """테스트 세션 종료 시 결과를 CSV로 저장"""
    if _test_results:
        # conftest.py는 backend/tests/에 있으므로, results 디렉토리는 같은 레벨에 생성
        conftest_dir = Path(__file__).parent
        output_dir = conftest_dir / "results"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = output_dir / f"test_results_{timestamp}.csv"
        
        fieldnames = ['test_name', 'status', 'duration', 'error', 'timestamp']
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(_test_results)
        
        print(f"\n테스트 결과가 CSV 파일로 저장되었습니다: {csv_path}")

