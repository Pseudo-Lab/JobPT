# Contributing Guide
> Last updated: 2025-10-29  
> Maintainer: DevFactory / JobPT Team

## 🧭 Git Branch Flow

이 프로젝트는 안정적인 배포와 유연한 개발을 위해 다음과 같은 브랜치 전략을 사용합니다.

| 브랜치 | 역할 | 비고 |
|---|---|---|
| `main` | 운영(Production) | 실제 배포된 안정 버전 |
| `dev` | 개발(Development) | 기능 통합 및 테스트 |
| `feat/*` | 기능 개발(Feature) | 새 기능 단위 개발 |
| `hotfix/*` | 긴급 수정(Hotfix) | 운영 중 빠른 버그 수정 |

### 브랜치 구조
```
main (배포)
  ↑
dev (개발)
  ↑
feat/* (기능개발)
hotfix/* (긴급수정) → main/dev 모두 가능
```

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

## ✅ Commit Message Convention (권장)

- `feat:` 새로운 기능 추가
- `fix:` 버그 수정
- `docs:` 문서 수정 (예: README, CONTRIBUTING)
- `style:` 코드 포맷팅, 세미콜론, 공백 등 (로직 변경 없음)
- `refactor:` 코드 리팩토링 (기능 동일, 내부 구조 개선)
- `test:` 테스트 코드 추가 또는 수정
- `chore:` 빌드, 패키지, 의존성 관리 등
- `ci:` CI/CD 설정 파일 변경 (GitHub Actions 등)

**예시 커밋:**
```bash
git commit -m "fix: resolve issue and merge back to dev"
git commit -m "docs: enforce PR-based workflow in contributing guide"
```

- 커밋 메시지는 **한글/영문 혼용**이 가능합니다.  
  - 예시: `docs: README.md 시스템 구조도 링크 추가 `

---

## 🔀 Pull Request & Merge Strategy

### 📝 PR 생성
- **모든 변경 사항은 Pull Request를 통해 제출해야 합니다.**
- PR의 제목은 하나의 대표 커밋 메시지처럼 작성하며, [Commit Message Convention](#-commit-message-convention)을 따르는 것을 권장합니다.
  - 예시: `feat: add resume feedback API`
- **PR 본문:** [Pull Request Template](.github/pull_request_template.md)에 따라 변경 내용, 관련 이슈 등을 상세히 기재합니다.

#### 브랜치별 PR 대상
- **`main` 브랜치:** `dev` 또는 `hotfix/*` 브랜치의 PR만 병합 가능
- **`dev` 브랜치:** `feat/*` 또는 `hotfix/*` 브랜치의 PR만 병합 가능

---

### 👀 리뷰 및 승인
- 모든 PR은 최소 **1명 이상의 리뷰어에게 승인**을 받아야 합니다.
- 리뷰어는 코드 리뷰 후 상태에 따라 `changes-requested` 또는 `approved` 라벨을 사용합니다.

#### 🏷️ 라벨 규칙
| 라벨 | 의미 | 담당자 |
|------|------|--------|
| `needs-review` | 리뷰 요청 상태 (자동) | - |
| `changes-requested` | 수정 요청 있음 | 리뷰어 |
| `approved` | 리뷰 승인 완료 — 머지 가능 | 리뷰어 |
| `merged` | 머지 완료 후 상태 표시 (자동) | - |

> ℹ️ `needs-review` 및 `merged` 라벨은 `.github/workflows/auto-label.yml`에서 GitHub Actions로 자동 처리됩니다.

---

### 🔄 병합 (Merge)

#### 병합 방식: Rebase & Merge
- 모든 PR은 **Rebase & Merge** 방식을 사용합니다.
- 커밋 히스토리를 **깔끔하고 직선적(linear)** 으로 유지하여 변경 추적성을 높입니다.

  ![Rebase & Merge 예시](https://cdn.hashnode.com/res/hashnode/image/upload/v1706952373414/31348a28-e662-428b-9f4b-5ac9a2d1ce55.png?auto=compress,format&format=webp)

#### 머지 전 필수 작업
1. **최신 베이스 브랜치로 Rebase**
  ```bash
    git fetch origin
    git rebase origin/dev   # 또는 origin/main
  ```
2. **충돌 해결** (발생 시)
   - Rebase 과정에서 충돌이 발생한 경우, **PR 작성자가 직접 해결**해야 합니다.
```bash
   # 충돌 해결 후
   git add <충돌_파일>
   git rebase --continue
   git push --force-with-lease origin <브랜치명>
```

#### 👥 Merge 주체
- 리뷰어가 `approved` 라벨을 부여하면, **PR 작성자 본인이 직접 머지**합니다.
- Merge 전에는 반드시 최신 베이스 브랜치 기준으로 **Rebase 및 충돌 여부를 확인**해야 합니다.

> ⚠️ **주의:** PR 진행 단계에 따라 반드시 라벨을 갱신하고, 머지 후에는 자동으로 `merged` 라벨이 적용됩니다.

---

### 🌿 브랜치 관리  
- 머지 완료 후에는 **해당 브랜치를 반드시 삭제(Delete branch after merge)** 합니다.  
- 불필요하게 오래된 `feat/*` 브랜치는 주기적으로 정리합니다.  
- `dev`와 `main` 브랜치는 직접 푸시(push)하지 않고, 반드시 **PR을 통해서만 변경**합니다.

---

## 📘 참고
- 자세한 서비스 구조 및 환경 설정은 [README.md](./README.md)를 참고하세요.
