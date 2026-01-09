import re
from typing import List, Dict, Tuple, Any


class HierarchicalSegmenter:
    """범용 계층적 문맥 보존 분리"""

    def __init__(
        self,
        min_chunk_length: int = 100,
        max_chunk_length: int = 300
    ):
        self.min_chunk_length = min_chunk_length
        self.max_chunk_length = max_chunk_length

    def segment(self, text: str) -> List[str]:
        if not text or len(text.strip()) < 10:
            return []
        
        has_markdown = self._has_markdown_structure(text)
        
        if has_markdown:
            return self._segment_markdown(text)
        else:
            return self._segment_plaintext(text)

    def _has_markdown_structure(self, text: str) -> bool:
        patterns = [
            r'^#{1,6}\s+',     
            r'^\s*[-*•]\s+',   
            r'\*\*.+?\*\*',    
            r'^---+$',         
        ]
        
        lines = text.split('\n')
        markdown_lines = 0
        
        for line in lines:
            for pattern in patterns:
                if re.search(pattern, line, re.MULTILINE):
                    markdown_lines += 1
                    break
        
        return (
            markdown_lines / max(len(lines), 1) > 0.4
            and re.search(r'^#{2,}', text, re.MULTILINE)
        )

    def _segment_markdown(self, text: str) -> List[str]:
        nodes = self.parse_markdown_hierarchy(text)
        chunks = self.create_contextualized_chunks(nodes)
        return chunks

    def _segment_plaintext(self, text: str) -> List[str]:
        # JD 특화 전처리
        text = re.sub(r'\|\s*', '\n\n', text)
        text = re.sub(r'•\s*', '\n\n', text)
        text = re.sub(r'\n{2,}', '\n\n', text)

        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            sentences = re.split(r'([.!?]\s+)', para)
            combined = [
                sentences[i] + (sentences[i+1] if i+1 < len(sentences) else '')
                for i in range(0, len(sentences), 2)
            ]

            for sent in combined:
                sent = sent.strip()
                if not sent:
                    continue

                tentative = f"{current_chunk} {sent}".strip() if current_chunk else sent

                if len(tentative) <= self.max_chunk_length:
                    current_chunk = tentative
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = sent

        if current_chunk:
            chunks.append(current_chunk)

        return chunks


    def _split_long_chunk(self, chunk: str) -> List[str]:
        if len(chunk) <= self.max_chunk_length:
            return [chunk]
        
        sentences = re.split(r'([.!?]\s+)', chunk)
        
        chunks = []
        current = ""
        
        for i in range(0, len(sentences), 2):
            if i + 1 < len(sentences):
                sent = sentences[i] + sentences[i+1]
            else:
                sent = sentences[i]
            
            if len(current) + len(sent) <= self.max_chunk_length:
                current += sent
            else:
                if current:
                    chunks.append(current.strip())
                current = sent
        
        if current:
            chunks.append(current.strip())
        
        return chunks
  
    def parse_markdown_hierarchy(self, text: str) -> List[Dict]:
        nodes = []
        context_stack = [None] * 5

        lines = text.split('\n')

        for line in lines:
            line_stripped = line.strip()

            if not line_stripped:
                continue

            if re.match(r'^[-=*_]{3,}$', line_stripped):
                continue

            level, node_type, content = self._parse_line(line_stripped)

            context_stack[level] = content

            for i in range(level + 1, 5):
                context_stack[i] = None

            current_context = [c for c in context_stack[:level] if c]

            nodes.append({
                'level': level,
                'type': node_type,
                'content': content,
                'context': current_context.copy() if current_context else []
            })

        return nodes

    def _parse_line(self, line: str) -> Tuple[int, str, str]:
        if line.startswith('## '):
            content = line[3:].strip()
            return (1, 'section', content)

        if line.startswith('### '):
            content = line[4:].strip()
            content = self._clean_markdown(content)
            return (2, 'company_or_project', content)

        if line.startswith('#### '):
            content = line[5:].strip()
            content = self._clean_markdown(content)
            return (3, 'subsection', content)

        if re.match(r'\d{4}\.\d{2}\s*[–-]\s*\d{4}\.\d{2}', line):
            return (3, 'period', line)

        if line.startswith('**') and ':**' in line:
            key_value = line.split(':**', 1)
            key = key_value[0].replace('**', '').strip()
            value = key_value[1].strip() if len(key_value) > 1 else ''
            return (3, f'meta_{key}', value)

        if line.startswith(('-', '*', '•')):
            content = re.sub(r'^[\-\*•]\s+', '', line)
            content = self._clean_markdown(content)
            return (4, 'task', content)

        content = self._clean_markdown(line)
        return (4, 'text', content)

    def _clean_markdown(self, text: str) -> str:
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'_(.+?)_', r'\1', text)
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
        text = re.sub(r'`(.+?)`', r'\1', text)
        return text.strip()

    def create_contextualized_chunks(self, nodes: List[Dict]) -> List[str]:
        chunks = []
        groups = self._group_by_context(nodes)

        for group in groups:
            context_prefix = group['context']
            tasks = group['tasks']
            metadata = group['metadata']

            if '기간' in metadata and metadata['기간']:
                context_prefix += f" ({metadata['기간']})"

            if '개요' in metadata and metadata['개요']:
                overview_chunk = f"{context_prefix} - 개요: {metadata['개요']}"
                if len(overview_chunk) >= self.min_chunk_length:
                    chunks.append(overview_chunk)

            if '기술' in metadata and metadata['기술']:
                tech_chunk = f"{context_prefix} - 기술: {metadata['기술']}"
                if len(tech_chunk) >= self.min_chunk_length:
                    chunks.append(tech_chunk)

            if '성과' in metadata and metadata['성과']:
                achievement_chunk = f"{context_prefix} - 성과: {metadata['성과']}"
                if len(achievement_chunk) >= self.min_chunk_length:
                    chunks.append(achievement_chunk)

            if not tasks:
                continue

            if len(tasks) == 1:
                chunk = f"{context_prefix}: {tasks[0]}"
                if len(chunk) >= self.min_chunk_length:
                    chunks.append(chunk)
            else:
                current_chunk_tasks = []
                current_length = len(context_prefix) + 2

                for task in tasks:
                    task_length = len(task) + 2
                    tentative_length = current_length + task_length

                    if tentative_length > self.max_chunk_length and current_chunk_tasks:
                        chunk_text = f"{context_prefix}: {'; '.join(current_chunk_tasks)}"
                        chunks.append(chunk_text)

                        current_chunk_tasks = [task]
                        current_length = len(context_prefix) + 2 + len(task)
                    else:
                        current_chunk_tasks.append(task)
                        current_length = tentative_length

                if current_chunk_tasks:
                    chunk_text = f"{context_prefix}: {'; '.join(current_chunk_tasks)}"
                    if len(chunk_text) >= self.min_chunk_length:
                        chunks.append(chunk_text)

        return chunks
    
    def _group_by_context(self, nodes: List[Dict]) -> List[Dict]:
        groups = []
        current_group = None

        for node in nodes:
            node_type = node['type']
            content = node['content']

            if node_type in ['company_or_project', 'section']:
                if current_group and (current_group['tasks'] or current_group['metadata']):
                    groups.append(current_group)

                current_group = {
                    'context': content,   # 예: "주요업무", "자격요건"
                    'tasks': [],
                    'metadata': {}
                }

            elif node_type == 'period' and current_group:
                current_group['context'] += f" ({content})"

            elif node_type.startswith('meta_') and current_group:
                meta_key = node_type.replace('meta_', '')
                current_group['metadata'][meta_key] = content

            elif node_type in ['task', 'text', 'subsection'] and current_group:
                if len(content) >= 5:
                    current_group['tasks'].append(content)

        if current_group and (current_group['tasks'] or current_group['metadata']):
            groups.append(current_group)

        return groups



if __name__ == '__main__':
    import sys
    
    segmenter = HierarchicalSegmenter(
        min_chunk_length=100,
        max_chunk_length=300
    )
    
    # 테스트 1: 마크다운 CV
    print("="*80)
    print("테스트 1: 마크다운 CV")
    print("="*80)
    try:
        with open('sample_cv.md', 'r', encoding='utf-8') as f:
            cv_text = f.read()
        
        chunks = segmenter.segment(cv_text)
        print(f" CV 청크 수: {len(chunks)}")
        print(f"\n첫 번째 청크:\n{chunks[0][:150]}...")
    except FileNotFoundError:
        print("⚠️ sample_cv.md 파일 없음")
    
    # 테스트 2: 평문 텍스트
    print("\n" + "="*80)
    print("테스트 2: 평문 JD 텍스트")
    print("="*80)
    
    jd_text = """
Backend Engineer
우리 회사는 핀테크 솔루션을 제공하는 스타트업입니다.
현재 백엔드 개발자를 찾고 있습니다.

주요 업무:
API 개발 및 유지보수를 담당합니다. 데이터베이스 설계 및 최적화가 필요합니다.
서버 아키텍처를 구축하고 관리합니다.

자격 요건:
Python 또는 Java 3년 이상 경험이 필요합니다.
RESTful API 설계 경험이 있어야 합니다.
AWS 또는 GCP 사용 경험을 우대합니다.
"""
    
    chunks = segmenter.segment(jd_text)
    print(f" JD 청크 수: {len(chunks)}")
    for i, chunk in enumerate(chunks, 1):
        print(f"\n청크 {i}:\n{chunk}")