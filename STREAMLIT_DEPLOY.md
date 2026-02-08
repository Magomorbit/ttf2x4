# TTF to EPDFont 변환기 - Streamlit 배포 가이드

## 🚀 로컬에서 실행

### 1. 패키지 설치
```bash
pip install -r requirements_streamlit.txt
```

### 2. 앱 실행
```bash
streamlit run streamlit_app.py
```

브라우저가 자동으로 열리며 `http://localhost:8501`에서 앱이 실행됩니다.

---

## ☁️ Streamlit Community Cloud에 배포

### 준비물
- GitHub 계정
- Streamlit 계정 (GitHub로 로그인 가능)

### 배포 단계

#### 1. GitHub 저장소 생성
1. GitHub에서 새 저장소 생성 (예: `ttf-to-epdfont-converter`)
2. 다음 파일들을 업로드:
   - `streamlit_app.py`
   - `requirements_streamlit.txt` → 이름을 `requirements.txt`로 변경
   - `README.md` (선택사항)

#### 2. Streamlit Community Cloud에 배포
1. [https://share.streamlit.io](https://share.streamlit.io) 접속
2. GitHub 계정으로 로그인
3. "New app" 클릭
4. 저장소 선택:
   - Repository: `your-username/ttf-to-epdfont-converter`
   - Branch: `main`
   - Main file path: `streamlit_app.py`
5. "Deploy!" 클릭

#### 3. 배포 완료
- 몇 분 후 앱이 배포됩니다
- 공개 URL이 생성됩니다 (예: `https://your-app.streamlit.app`)
- 이 URL을 누구나 사용할 수 있습니다!

---

## 📁 필요한 파일 구조

```
your-repository/
├── streamlit_app.py          # 메인 앱 파일
├── requirements.txt           # Python 패키지 (requirements_streamlit.txt를 이름 변경)
└── README.md                  # 프로젝트 설명 (선택사항)
```

---

## ⚙️ 고급 설정 (선택사항)

### packages.txt 생성
시스템 레벨 패키지가 필요한 경우:

```
libfreetype6-dev
```

### .streamlit/config.toml
앱 설정 커스터마이징:

```toml
[theme]
primaryColor = "#667eea"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[server]
maxUploadSize = 50
```

---

## 🔧 문제 해결

### 배포 실패 시
1. `requirements.txt` 파일명 확인
2. Python 버전 호환성 확인 (3.7-3.11 권장)
3. Streamlit Community Cloud 로그 확인

### 메모리 부족 오류
- Community Cloud는 1GB RAM 제한이 있습니다
- 큰 폰트 파일은 처리에 시간이 걸릴 수 있습니다

---

## 📝 GitHub 저장소 예시

### README.md
```markdown
# TTF to EPDFont Converter

Web application to convert TTF/OTF fonts to .epdfont format for E-Paper displays.

## Features
- Web-based GUI using Streamlit
- Support for TTF/OTF fonts
- 1-bit (B&W) and 2-bit (4-level grayscale) modes
- Advanced typography options

## Live Demo
🔗 [Try it now!](https://your-app.streamlit.app)

## Run Locally
\`\`\`bash
pip install -r requirements.txt
streamlit run streamlit_app.py
\`\`\`
```

---

## 🌐 무료 배포 옵션 비교

| 플랫폼 | 장점 | 단점 |
|--------|------|------|
| **Streamlit Community Cloud** | 무료, 쉬운 배포, GitHub 연동 | 1GB RAM 제한 |
| **Hugging Face Spaces** | 무료, 좋은 성능 | 설정이 조금 복잡 |
| **Railway** | 무료 티어 있음 | 무료 시간 제한 |
| **Render** | 무료 티어 있음 | 콜드 스타트 느림 |

**추천**: Streamlit Community Cloud (가장 간단하고 Streamlit에 최적화)

---

## ✅ 체크리스트

배포 전 확인사항:
- [ ] `streamlit_app.py` 파일 준비
- [ ] `requirements_streamlit.txt`를 `requirements.txt`로 이름 변경
- [ ] GitHub 저장소에 파일 업로드
- [ ] Streamlit Community Cloud 계정 생성
- [ ] 앱 배포 및 테스트

---

## 📞 지원

문제가 있으시면:
1. Streamlit 문서: https://docs.streamlit.io
2. Streamlit 커뮤니티: https://discuss.streamlit.io
3. GitHub Issues에 문의
