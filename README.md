# BlastTap 6.0 AI Smart Control System

🔥 고로 출선 AI 실시간 수지추적 시스템 v6.0

## 📌 시스템 개요

BlastTap 6.0은 고로조업 현장에서 장입-생성-출선-저선-경보-AI보정까지 실시간으로 관리할 수 있는 
AI 기반 고로조업 통합관리 엔진입니다.

- 실시간 장입수지 추적
- AI 환원효율 자동보정
- 저선량 및 저선율 계산
- AI 목표 용선온도 자동계산
- TAP 진행 및 공취예상
- 비트경 및 출선간격 AI 추천
- 실시간 시각화 및 누적 리포트 기록

---

## 📦 주요 파일 구성

| 파일 | 설명 |
|---|---|
| `app.py` | Streamlit 실행용 메인 소스코드 |
| `requirements.txt` | 필요한 파이썬 패키지 목록 |
| `blasttap-6.0-technical-specs.pdf` | 전체 기술명세서 (수식 및 계산근거) |
| `sample_report.csv` | 샘플 누적조업 리포트 |
| `blasttap-6.0-package.zip` | 전체 패키지 압축파일 |

---

## 🚀 설치 및 실행 방법

### 로컬 환경에서 실행:

```bash
# 가상환경 추천
python -m venv venv
source venv/bin/activate  # (Windows는 venv\Scripts\activate)

# 패키지 설치
pip install -r requirements.txt

# 실행
streamlit run app.py