# 중랑AX 인사이트 제작키트

중랑구청 중랑AI혁신팀의 주간 연재물 「중랑AX 인사이트」(매주 목요일, 새올게시판 › 기획예산과)를 만드는 키트입니다.

- `build_v2.py` : 카드뉴스 PDF·PNG (`python3 build_v2.py 회차/회차NN_v2.json`)
- `build_video.py` : 설명 동영상 (`python3 build_video.py 데이터.json 대본.json audio|stills|video|remix`)
- `매주_제작순서.md` : 매주 만드는 순서 (예약 작업이 따르는 문서)
- `제작가이드.md` : 디자인·문체·선정 기준·배경음악 순서
- `회차/` : 회차별 데이터(json)·게시글 본문. 회차01이 표준 예시
- `chars/`, `slogan_white2.png`, `PretendardVariable.woff2`, `bgm/01~14.mp3` : 제작 재료

필요: `pip install -r requirements.txt`, google-chrome, ffmpeg
