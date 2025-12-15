#!/usr/bin/env python3
"""
JD URL 크롤러 - 간단한 CLI 도구

사용법:
    python3 backend/util/demo_crawl_url.py <URL>
    python3 backend/util/demo_crawl_url.py https://www.saramin.co.kr/zf_user/jobs/relay/view?isMypage=no&rec_idx=52554116&recommend_ids=eJxtz8sRwjAMBNBquEva1e9MIem%2FCwgTHJnh%2BCyPduVm3d55lOYjn25OptTRYj88%2BHmgaUSs75LRxCIQabbIUOv4w2sZioFcYTfXXLx7douK2e3itxsFNuJOYqPWvUyl590w840OTrJ8m%2Fo4880tCITuNeTkCwNGT3g%3D&view_type=etc&gz=1&t_ref_content=banner&t_ref=view_delete&relayNonce=7f8030cbbed0ae057f36&immediately_apply_layer_open=n
    
    # 파일로 저장하려면:
    python3 backend/util/demo_crawl_url.py <URL> --save
"""

import sys
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.util.jd_crawler import crawl_jd_from_url


def save_to_file(url, result):
    """결과를 파일로 저장"""
    output_dir = Path.cwd() / "scraped_jd"
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    site_name = result.get('site', 'unknown').replace(' ', '_')
    filename = f"{site_name}_{timestamp}.txt"
    filepath = output_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"URL: {url}\n")
        f.write(f"사이트: {result['site']}\n")
        f.write(f"성공 여부: {result['success']}\n")
        f.write(f"에러: {result['error']}\n")
        f.write(f"텍스트 길이: {len(result['text'])} 자\n")
        f.write("=" * 80 + "\n\n")
        f.write(result['text'])
    
    return filepath


def main():
    """메인 함수"""
    if len(sys.argv) < 2:
        print("사용법: python3 backend/util/demo_crawl_url.py <URL> [--save]")
        print("\n예시:")
        print("  python3 backend/util/demo_crawl_url.py https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=12345")
        print("  python3 backend/util/demo_crawl_url.py <URL> --save  # 파일로 저장")
        sys.exit(1)
    
    url = sys.argv[1]
    save_file = '--save' in sys.argv
    
    print("\n" + "=" * 80)
    print(f"  JD URL 크롤링")
    print("=" * 80)
    print(f"\n📌 URL: {url}\n")
    
    try:
        result = crawl_jd_from_url(url)
        
        print("─" * 80)
        if result['success']:
            print(f"✅ 성공")
            print(f"🏢 사이트: {result['site']}")
            print(f"📝 텍스트 길이: {len(result['text'])} 자")
            
            if save_file:
                filepath = save_to_file(url, result)
                print(f"💾 파일 저장: {filepath}")
                print("\n" + "─" * 80)
                print("📄 추출된 텍스트 (처음 500자):")
                print("─" * 80)
                print(result['text'][:500])
                if len(result['text']) > 500:
                    print(f"\n... (총 {len(result['text'])}자, 전체는 파일 참조)")
                print("─" * 80)
            else:
                print("\n" + "─" * 80)
                print("📄 추출된 텍스트:")
                print("─" * 80)
                print(result['text'])
                print("─" * 80)
                print(f"\n💡 전체 텍스트를 파일로 저장하려면: --save 옵션을 추가하세요")
        else:
            print(f"❌ 실패")
            print(f"🏢 사이트: {result['site']}")
            print(f"⚠️  에러: {result['error']}")
            print("─" * 80)
    
    except Exception as e:
        print(f"❌ 예외 발생: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
