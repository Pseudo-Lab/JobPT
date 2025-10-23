# Contributing Guide
> Last updated: 2025-10-23
> Maintainer: DevFactory / JobPT Team

## 🧭 Git Branch Flow

이 프로젝트는 안정적인 배포와 유연한 개발을 위해 다음과 같은 브랜치 전략을 사용합니다.

| 브랜치 | 역할 | 비고 |
|---|---|---|
| `main` | 운영(Production) | 실제 배포된 안정 버전 |
| `dev` | 개발(Development) | 기능 통합 및 테스트 |
| `feat/*` | 기능 개발(Feature) | 새 기능 단위 개발 |
| `hotfix/*` | 긴급 수정(Hotfix) | 운영 중 빠른 버그 수정 |

---

## ⚙️ Development Workflow

### 1. 기능 개발 (feat/*)
- `dev` 브랜치에서 새로운 기능 브랜치를 생성합니다.
  ```bash
  git checkout dev
  git checkout -b feat/{feature-name}
  ```
- `feat` 브랜치는 `feat/{feature-name}` 형식으로 네이밍합니다.
- 기능 구현 완료 후, `dev` 브랜치로 Pull Request(PR)를 생성합니다.

### 2. 배포 (dev → main)
- `dev` 브랜치에서 모든 기능 통합 및 테스트가 완료되면, `main` 브랜치로 배포 PR을 생성합니다.
- PR 제목은 `release: merge dev to main (production deploy)`와 같은 형식을 사용합니다.
- PR이 승인되고 병합되면 `main` 브랜치에 코드가 반영되며, 자동 배포가 실행됩니다.

### 3. 긴급 수정 (hotfix/*)
- `main` 브랜치에서 `hotfix` 브랜치를 생성합니다.
  ```bash
  git checkout main
  git checkout -b hotfix/{issue-name}
  ```
- 수정 완료 후, `main`과 `dev` 브랜치로 각각 PR을 생성하여 변경 사항을 반영합니다.

---

## ✅ Commit Message Convention

- `feat:` 새로운 기능 추가
- `fix:` 버그 수정
- `docs:` 문서 수정 (예: README, CONTRIBUTING)
- `chore:` 빌드, 패키지, 설정, 의존성 등 관리성 변경 (비즈니스 로직 영향 없음)
- `refactor:` 코드 리팩토링

**예시 커밋:**
```bash
git commit -m "fix: resolve issue and merge back to dev"
git commit -m "docs: enforce PR-based workflow in contributing guide"
```

---

## 🔀 Pull Request & Merge Rules

### Pull Request 생성
- **모든 변경 사항은 Pull Request를 통해 제출해야 합니다.**
- `main`과 `dev` 브랜치는 Protected Branch로 설정되어 있어 직접적인 Push가 불가능합니다.
- PR의 제목은 하나의 대표 커밋 메시지처럼 작성하며, [Commit Message Convention](#-commit-message-convention)을 따르는 것을 권장합니다.
  - 예시: `feat: add resume feedback API`
- **PR 본문:** [Pull Request Template](.github/pull_request_template.md)에 따라 변경 내용, 관련 이슈 등을 상세히 기재합니다.

### 리뷰 및 승인
- 모든 PR은 최소 **1명 이상의 리뷰어에게 승인**을 받아야 합니다.
- **CI 통과 필수** (`lint`, `test`, `build` 단계 모두 성공해야 함).
- 리뷰어는 PR 라벨을 통해 상태를 명시합니다 (`needs-review`, `changes-requested`, `approved`).
- PR 작성자는 리뷰 요청 시 `needs-review` 라벨을, 리뷰어는 리뷰 후 상태에 따라 
  `changes-requested` 또는 `approved` 라벨을 사용합니다.

### 병합 규칙
- **`main` 브랜치:** `dev` 또는 `hotfix/*` 브랜치의 PR만 병합할 수 있습니다.
- **`dev` 브랜치:** `feat/*` 또는 `hotfix/*` 브랜치의 PR만 병합할 수 있습니다.
- **Rebase & merge**를 권장하여 커밋 히스토리를 깔끔하게 유지합니다.
  - ![Rebase & Merge 예시](https://cdn.hashnode.com/res/hashnode/image/upload/v1706952373414/31348a28-e662-428b-9f4b-5ac9a2d1ce55.png?auto=compress,format&format=webp)
- 병합 후에는 브랜치를 **삭제하는 것을 권장**합니다 (`Delete branch after merge` 옵션 사용).

---

## 📘 참고
- 자세한 서비스 구조 및 환경 설정은 [README.md](./README.md)를 참고하세요.
