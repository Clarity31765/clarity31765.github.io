# oliverlee.me

개인 사이트 소스. HTML·CSS만으로 만든 정적 사이트라 빌드 과정이 없고, 외부 폰트·스크립트를 쓰지 않아 중국에서도 같은 방식으로 열립니다.

```
index.html                     홈 (소개·경력·툴킷·글·AI 활용)
notes/detection-limits.html    첫 글: Currie / EPA MDL / SEMI C10 비교
assets/style.css               전체 스타일 (색·글꼴 토큰은 파일 맨 위)
assets/favicon.svg             탭 아이콘
404.html                       없는 주소로 들어왔을 때
CNAME                          oliverlee.me 연결용 (지우지 말 것)
.nojekyll                      GitHub의 Jekyll 변환을 끄는 빈 파일 (지우지 말 것)
robots.txt, sitemap.xml        검색엔진용
```

---

## 1. 올리기 전에 채울 것

파일에서 아래 문자열을 찾아 바꿔주세요 (메모장·VS Code의 "찾기/바꾸기").

| 찾을 문자열 | 바꿀 내용 | 위치 |
|---|---|---|
| `REPLACE_BEFORE` / `REPLACE_AFTER` | AI 활용 전후 시간 (모르면 그 두 줄 삭제) | index.html |

- 경력의 직함·기간은 2026년 6월 이력서(Resume_DongChoonLee_Oliver.docx) 기준으로 채웠습니다. 이후 바뀐 게 있으면 수정하세요.
- 이력서 PDF는 올리지 않습니다. 공개 저장소에 올린 파일은 링크가 없어도 누구나 GitHub에서 받을 수 있기 때문입니다. 사이트에서는 "CV on request"로 이메일 요청을 받습니다.
- 사이트는 공개 저장소에 올라가므로 **회사 내부 데이터·기밀 표기는 절대 넣지 마세요.**

## 2. GitHub에 올리기 (브라우저만으로 가능)

1. GitHub 우측 상단 **+ → New repository**
2. 이름을 정확히 **`사용자명.github.io`** (전부 소문자)로, **Public** 선택 → **Create repository**
   - 무료 계정은 공개 저장소에서만 Pages가 동작합니다.
3. 저장소 화면에서 **Add file → Upload files** → 이 폴더 안의 **내용물 전체**를 끌어다 놓기 → **Commit changes**
   - `.nojekyll`처럼 점으로 시작하는 파일은 숨김 파일이라 안 보일 수 있습니다. 업로드 후 목록에 없으면 **Add file → Create new file**로 이름만 `.nojekyll`인 빈 파일을 만들어주세요.
4. **Settings → Pages** → Source에서 브랜치 **main**, 폴더 **/ (root)** → **Save**
5. 최대 10분 뒤 `https://사용자명.github.io` 에서 열리는지 확인

## 3. oliverlee.me 연결 (순서 중요)

GitHub 공식 문서 권장 순서입니다. **DNS부터 바꾸지 마세요** — GitHub에 먼저 등록하지 않으면 남이 서브도메인을 가로챌 수 있습니다.

**3-1. 도메인 소유 인증**
1. GitHub 프로필 사진 → **Settings → Pages → Add a domain** → `oliverlee.me` 입력
2. GitHub가 알려주는 **TXT 레코드**를 가비아 DNS에 추가
   - 이름(호스트): `_github-pages-challenge-사용자명`
   - 값: GitHub 화면에 나온 문자열
3. 반영되면(즉시~24시간) **Verify** 클릭. 이 TXT 레코드는 **지우지 말고 유지**.

**3-2. 저장소에 도메인 지정**
- 저장소 **Settings → Pages → Custom domain**에 `oliverlee.me` 입력 → Save
  (CNAME 파일이 이미 들어있어서 자동으로 채워져 있을 수도 있습니다.)

**3-3. 가비아 DNS 레코드**

| 타입 | 호스트 | 값 |
|---|---|---|
| A | @ | 185.199.108.153 |
| A | @ | 185.199.109.153 |
| A | @ | 185.199.110.153 |
| A | @ | 185.199.111.153 |
| CNAME | www | 사용자명.github.io. |

- 가비아가 기본으로 넣어둔 A/CNAME 레코드(파킹 페이지 등)가 있으면 먼저 삭제.
- `*` (와일드카드) 레코드는 만들지 마세요. 도메인 탈취 위험이 있다고 GitHub가 경고합니다.

**3-4. HTTPS**
- 연결 후 Settings → Pages의 **Enforce HTTPS** 체크 (활성화까지 최대 24시간).

## 4. 올린 뒤 확인

- [ ] `https://oliverlee.me` 와 `https://www.oliverlee.me` 둘 다 열림
- [ ] 휴대폰에서 열어 경력·글 목록이 한 줄로 쌓이는지
- [ ] CV (PDF) 링크가 열리는지
- [ ] 없는 주소(`/abc`)에서 404 페이지가 뜨는지
- [ ] 중국에 있는 지인이나 헤드헌터에게 열리는지 한 번 확인 요청
- [ ] LinkedIn 연락처 정보 → 웹사이트에 `https://oliverlee.me` 추가

## 5. 글 추가하는 법

1. `notes/detection-limits.html`을 복사해 `notes/새-글-이름.html`로 저장
2. `<title>`, `description`, `canonical`, 본문을 교체
3. `index.html`의 `<ul class="posts">` 안에 `<li>` 하나를 복사해 날짜·제목·요약·링크 수정
4. `sitemap.xml`에 `<url>` 한 줄 추가

## 6. 고쳐 쓰기

- 색을 바꾸려면 `assets/style.css` 맨 위 `:root`의 값만 바꾸면 전체에 반영됩니다. 강조색은 `--plasma`.
- 사이드바 스펙트럼 그림은 예시용 그래프(실제 측정 데이터 아님)이며, 페이지 캡션에도 그렇게 적혀 있습니다.
