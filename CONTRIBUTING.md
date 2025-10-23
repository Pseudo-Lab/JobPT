# Contributing Guide
> Last updated: 2025-10-19  
> Maintainer: DevFactory / JobPT Team

## 🧭 Git Branch Flow

이 프로젝트는 안정적인 배포와 유연한 개발을 위해 다음과 같은 브랜치 전략을 사용합니다.

| 브랜치 | 역할 | 비고 |
|--------|------|------|
| `main` | 운영(Production) | 실제 배포된 안정 버전 |
| `dev` | 개발(Development) | 기능 통합 및 테스트 |
| `release/x.y.z` | 배포 준비(Release Candidate) | QA 및 안정화 단계 |
| `feature/*` | 기능 개발(Feature) | 새 기능 단위 개발 |
| `hotfix/*` | 긴급 수정(Hotfix) | 운영 중 빠른 버그 수정 |

---

## ⚙️ Workflow

1. **기능 개발**
   ```bash
   git checkout dev
   git checkout -b feature/{feature-name}
   ```
   - 기능 구현 완료 후 반드시 **Pull Request(PR)** 를 생성하여 `dev`에 병합합니다.  
   - 직접 push나 merge는 금지합니다.

2. **릴리스 준비**
   ```bash
   git checkout dev
   git checkout -b release/x.y.z
   ```
   > 릴리스 브랜치 네이밍은 `release/{major}.{minor}.{patch}` 형태로 통일합니다.  
   > 예시: `release/1.3.0`
   
   - QA, 문서 수정, 버그 수정 등 **배포 전 안정화 작업**을 진행합니다.  
   - **원칙적으로 수정은 `dev`에서 먼저 진행**하고, 필요한 커밋만 `release/x.y.z`에 `cherry-pick`합니다.  
   - 부득이하게 `release/x.y.z`에서 직접 수정한 경우, **반드시 수정 내용을 `release/x.y.z → dev`로 병합(cherry-pick 또는 merge)** 하여 개발계와의 차이를 방지해야 합니다.  
   - 릴리스 완료 후에는 **`release/x.y.z → main`으로 PR을 생성**하고, 승인 후 병합합니다.  
   - 배포 완료 후 태그를 생성하고, **`release/x.y.z → dev` PR** 을 통해 양쪽 동기화를 보장합니다.

3. **배포 (PR 기반)**
   - `release/x.y.z` → `main`으로 Pull Request를 생성합니다.
   - PR 제목 예시:  
     `release: merge 1.2.0 to main (production deploy)`
   - 리뷰 및 CI 통과 후 PR이 병합되면 **자동 배포**가 실행됩니다.
   - 모든 배포는 **PR 기반으로만 진행**되며, `main`에 직접 push는 금지됩니다.

4. **긴급 수정 (Hotfix)**
   ```bash
   git checkout main
   git checkout -b hotfix/{issue-name}
   ```
   - 수정 후 반드시 **PR을 통해** `main`에 병합하고, **동일한 커밋을 `dev`에도 PR로 반영**합니다.  
   - 직접 push는 금지합니다.

---

## 🪶 Merge 규칙

- 모든 브랜치는 **직접 push 금지**, PR을 통해서만 병합 가능  
- 모든 PR은 **리뷰 1인 이상 승인** 필수  
- `main`에는 오직 `release` 혹은 `hotfix` 브랜치에서 생성된 PR만 허용  
- `release`에서 수정된 커밋은 반드시 `dev`에도 반영해야 함 (별도 PR 또는 merge)  
- 커밋 메시지 컨벤션:
  - `feat:` 새로운 기능 추가  
  - `fix:` 버그 수정  
  - `docs:` 문서 수정 (예: README, CONTRIBUTING)  
  - `chore:` 빌드, 패키지, 설정, 의존성 등 관리성 변경 (비즈니스 로직 영향 없음)
  - `refactor:` 코드 리팩토링  

> `main`, `release/*`, `dev` 브랜치는 **Protected Branch** 로 설정되어 있으며,  
> 모든 변경은 Pull Request를 통해서만 반영해야 합니다.

---

## ✅ 예시 커밋

```bash
git commit -m "fix: resolve issue in release and merge back to dev"
git commit -m "docs: enforce PR-based workflow in contributing guide"
```

---

## 🔀 Pull Request 규칙

- 모든 변경은 반드시 **Pull Request(PR)** 를 통해 제출해야 합니다.
- 직접 push는 금지되며, CI 통과 및 리뷰 승인 후 병합 가능합니다.

  1. **PR 제목 규칙**
     - `feat:` 새 기능 추가
     - `fix:` 버그 수정
     - `docs:` 문서 변경
     - `chore:` 설정 변경
     - `refactor:` 리팩토링
     - 예시: `feat: add resume feedback API`

  2. **PR 본문 템플릿 (예시)**
     - **요약:** 변경된 내용 간략히 설명
     - **관련 이슈:** `#123` 형식으로 연결
     - **테스트:** 어떤 방식으로 테스트했는지 명시
     - **스크린샷 (선택):** UI 변경이 있을 경우 첨부  
     > PR 작성 시 [Pull Request Template](.github/pull_request_template.md)이 자동 적용됩니다.

  3. **리뷰 및 승인**
     - 최소 **1명 이상 리뷰 승인 필수**
     - **CI 통과 필수** (`lint`, `test`, `build` 단계 모두 성공해야 함)
     - 리뷰어는 **PR 라벨**을 통해 역할 구분:
       - `needs-review`: 리뷰 대기
       - `changes-requested`: 수정 요청
       - `ready-to-merge`: 병합 가능 상태  
     > 모든 PR은 CI/CD 워크플로 (`ci.yml`) 성공 시에만 병합 가능합니다.

  4. **병합 기준**
     - `main`: 오직 `release/*` 또는 `hotfix/*` PR만 허용  
     - `dev`: `feature/*` → `dev` 병합만 허용  
     - **Squash & merge** 권장 (히스토리 단순화)
     - 병합 후 브랜치는 **삭제 권장** (`Delete branch after merge` 옵션 사용)

---

## ✅ 예시 PR 제목
- `feat: add LLM-based resume matching service`
- `fix: resolve issue in job description parser`
- `docs: update branch strategy and CI workflow`

## 📘 참고
- 자세한 서비스 구조 및 환경 설정은 [README.md](./README.md)를 참고하세요.
