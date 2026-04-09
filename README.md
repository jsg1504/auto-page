# Auto Page

GitHub issue를 문서화 요청으로 받아 OpenAI Responses API(`gpt-5.4`)로 문서를 생성하고, 카테고리별 Markdown을 커밋해 GitHub Pages에 반영하는 자동화 프로젝트입니다.

## 기본 흐름

1. 사용자가 `Documentation request` 이슈 템플릿으로 요청을 생성합니다.
2. `doc-request-opened` workflow가 `state:needs-review` 라벨을 붙입니다.
3. 허용된 reviewer/admin 이 `state:review-complete` 라벨을 붙입니다.
4. `doc-request-review-complete` workflow가 OpenAI로 문서를 생성하고 `docs/` 트리에 반영한 뒤 커밋/푸시합니다.
5. `pages-build` workflow가 GitHub Pages용 사이트를 배포합니다.
6. 실패 시 이슈에 실패 이유를 남기고 `state:failed` 로 전환합니다.
7. 사용자가 내용을 수정하고 `state:retry-requested` 라벨을 붙이면 다시 검수 상태로 되돌립니다.

## 필요한 GitHub 설정

- `OPENAI_API_KEY` secret: OpenAI API key
- `REVIEWER_POOL` secret: 문서 생성 권한이 있는 GitHub 로그인 목록(쉼표 또는 줄바꿈 구분)
- 선택: `REQUESTER_POOL` secret + `ENFORCE_REQUESTER_POOL=true` variable
- GitHub Pages: `Settings > Pages > Build and deployment > Source = GitHub Actions`
- 선택: `PAGES_ADMIN_TOKEN` secret
  - 저장소에 Pages가 아직 한 번도 활성화되지 않았다면 필요합니다.
  - `actions/configure-pages`의 `enablement`는 기본 `GITHUB_TOKEN`으로는 동작하지 않아서, repo admin 권한이 있는 PAT 또는 적절한 GitHub App 토큰을 넣어야 합니다.

## 로컬 검증

```bash
python -m unittest discover -s tests -v
python -m compileall app scripts tests
```

## 구조

- `app/`: 핵심 상태 머신, 이슈 파서, OpenAI adapter, 카테고리/문서 작성, git publishing 로직
- `scripts/run_workflow.py`: GitHub Actions에서 호출하는 entrypoint
- `.github/workflows/`: issue opened / review complete / retry / pages deploy workflows
- `docs/`: GitHub Pages로 배포되는 Markdown 문서 트리
- `tests/`: fixture 기반 단위/통합 테스트


## 라벨 규칙

- `doc-request` 는 이 자동화 흐름의 **영구 분류 라벨**이다. reviewed/retry/generation workflow 는 이 라벨이 없는 이슈에는 반응하지 않는다.
- 상태 라벨(`state:*`)은 항상 하나만 존재해야 한다.
- 자동 상태 전이는 이슈 comment 에 machine-readable marker(`<!-- auto-page:state=... -->`)를 남겨 감사/audit 용 메타데이터로 기록한다. 이 marker 는 운영 추적용이며, 생성 전이의 권한 판단 자체는 상태 라벨과 reviewer pool 검증이 담당한다.

## 브랜치 보호 / 배포 정책

기본 구현은 GitHub Actions가 문서 변경을 직접 커밋/푸시하는 흐름을 가정합니다.
브랜치 보호로 기본 브랜치 직접 푸시가 금지되어 있다면 다음 중 하나를 명시적으로 선택해야 합니다.

- 전용 deploy branch 사용
- Actions bot의 제한적 bypass 허용
- PR 기반 publish 흐름으로 전환

즉, `GITHUB_TOKEN` 기본 동작에만 기대지 말고 저장소 정책과 함께 맞춰야 합니다.
