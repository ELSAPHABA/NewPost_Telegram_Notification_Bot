# NewPost Telegram Notification Bot

여러 웹사이트의 최신 게시글, 캐시백, 가격 조건을 주기적으로 확인하고 새 알림을 Telegram으로 보내는 봇입니다.

## 주요 기능

- Telegram Bot polling 기반 실행
- `/start` 명령 또는 임의 명령 수신 시 chat id 자동 등록
- 등록된 chat id를 `chat_ids.json`에 저장
- 기본 30초 주기로 watcher 실행
- watcher 최대 동시 실행 수 제한
- User-Agent 주기적 로테이션
- 선택적 HTTP/HTTPS proxy 사용
- Docker 컨테이너 실행 지원
- GitHub Actions를 통한 RPi3 SSH 배포 지원

## 감시 대상

| Watcher | 대상 | 알림 조건 |
| --- | --- | --- |
| `MiniPCWatcher` | DCInside MiniPC 갤러리 | 최신 게시글 ID 변경 |
| `SFFWatcher` | DCInside SFF 갤러리 | 최신 게시글 ID 변경 |
| `TwoCPUWatcher` | 2CPU 하드웨어 게시판 | 최신 게시글 ID 변경 |
| `SBNordVPNWatcher` | ShopBack NordVPN | 캐시백 95% 이상 도달 |
| `SBSurfsharkWatcher` | ShopBack Surfshark | 캐시백 95% 이상 도달 |
| `SSAdguardWatcher` | StackSocial AdGuard | 가격이 14달러 미만 도달 |

## 동작 구조

```text
main.py
  -> config.py에서 실행 설정 로드
  -> ChatIdManager가 chat_ids.json 관리
  -> UserAgentManager가 user-agents.txt에서 User-Agent 선택
  -> WatcherManager가 watcher들을 주기적으로 실행
  -> SiteWatcher.fetch_response()가 requests 요청 수행
  -> 새 항목 또는 조건 충족 시 Telegram 메시지 전송
```

`WatcherManager`는 `asyncio.Semaphore`와 `asyncio.gather`를 사용해 watcher를 병렬 실행합니다. 기본 동시 실행 수는 3개이며, `WATCHER_WORKER_COUNT`로 조정할 수 있습니다.

각 watcher의 실제 HTTP 요청은 동기 `requests` 기반이므로 `asyncio.to_thread()`로 event loop 밖에서 실행됩니다. 이전 실행이 아직 끝나지 않은 경우 다음 주기 작업은 중복 실행하지 않고 건너뜁니다.

## 요구 사항

- Python 3.10 이상
- Telegram Bot Token
- `user-agents.txt`

Python 의존성은 `pyproject.toml`에 정의되어 있습니다.

```text
python-telegram-bot[job-queue]
beautifulsoup4
requests[socks]
python-dotenv
```

## 환경 변수

| 이름 | 기본값 | 설명 |
| --- | --- | --- |
| `TELEGRAM_BOT_TOKEN` | 없음 | 필수. Telegram Bot Token |
| `TZ` | `UTC` | 컨테이너 및 봇 기준 시간대 (예: `Asia/Seoul`, `UTC`) |
| `CHAT_IDS_FILE` | `chat_ids.json` | chat id 저장 파일 경로 |
| `USER_AGENTS_FILE` | `user-agents.txt` | User-Agent 목록 파일 경로 |
| `USER_AGENT_ROTATE_INTERVAL` | `20` | watcher 확인 횟수 기준 User-Agent 변경 주기 |
| `WATCHER_WORKER_COUNT` | `3` | 동시에 실행할 watcher 수 |
| `PROXY_ENABLED` | `false` | proxy 사용 여부 |
| `PROXY_USER` | 없음 | proxy 계정 |
| `PROXY_PASS` | 없음 | proxy 비밀번호 |
| `PROXY_HOST_1` ~ `PROXY_HOST_12` | 없음 | proxy host 목록 |
| `PROXY_PORT` | 없음 | proxy port |
| `PROXY_ROTATE_SECONDS` | `1800` | proxy host 변경 주기, 초 단위 |

Boolean 값은 `1`, `true`, `yes`, `on`, `0`, `false`, `no`, `off`를 사용할 수 있습니다.

## `.env` 예시

```env
TELEGRAM_BOT_TOKEN=123456789:replace_me
TZ=UTC

USER_AGENT_ROTATE_INTERVAL=20
WATCHER_WORKER_COUNT=3

PROXY_ENABLED=false
PROXY_USER=
PROXY_PASS=
PROXY_HOST_1=
PROXY_PORT=
PROXY_ROTATE_SECONDS=1800
```

proxy를 켜려면 다음처럼 설정합니다.

```env
PROXY_ENABLED=true
PROXY_USER=proxy-user
PROXY_PASS=proxy-password
PROXY_HOST_1=proxy1.example.com
PROXY_HOST_2=proxy2.example.com
PROXY_PORT=8080
PROXY_ROTATE_SECONDS=900
```

host 값에 `http://` 같은 scheme이 들어가도 내부에서 제거합니다. `requests`에는 `http://user:pass@host:port` 형태로 전달됩니다.

## 로컬 실행

```bash
python -m venv .venv
source .venv/bin/activate
pip install .
python main.py
```

Windows PowerShell에서는 가상환경 활성화 명령만 다릅니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install .
python main.py
```

## Docker 실행

이미지 빌드:

```bash
docker build -t newpost-telegram-notification-bot .
```

chat id를 유지할 Docker volume 생성:

```bash
docker volume create NewPost_Telegram_Notification_bot-data
```

컨테이너 실행:

```bash
docker run -d \
  --name NewPost_Telegram_Notification_bot \
  --restart unless-stopped \
  --env-file .env \
  -v NewPost_Telegram_Notification_bot-data:/data \
  newpost-telegram-notification-bot
```

Docker 컨테이너에서는 기본적으로 `/data/chat_ids.json`이 생성되고, `/app/chat_ids.json`은 해당 파일을 가리키는 symlink가 됩니다.

로그 확인:

```bash
docker logs -f NewPost_Telegram_Notification_bot
```

컨테이너 중지 및 제거:

```bash
docker rm -f NewPost_Telegram_Notification_bot
```

## GitHub Actions 배포

[`.github/workflows/RPi3.yml`](.github/workflows/RPi3.yml)은 `main` 브랜치 push 시 RPi3 서버에 SSH로 접속해 Docker 이미지를 빌드하고 컨테이너를 재생성합니다.

배포 대상 서버의 프로젝트 경로 예시:

```text
/path/to/NewPost_Telegram_Notification_Bot
```

workflow에서 사용하는 Docker 이름:

| 항목 | 값 |
| --- | --- |
| 이미지 | `newpost-telegram-notification-bot` |
| 컨테이너 | `NewPost_Telegram_Notification_bot` |
| 볼륨 | `NewPost_Telegram_Notification_bot-data` |

### GitHub Secrets

배포용 SSH secret:

```text
RPI3_SERVER_HOST
RPI3_SERVER_USER
RPI3_SSH_PRIVATE_KEY
```

봇 및 proxy secret:

```text
TELEGRAM_BOT_TOKEN
TZ
PROXY_USER
PROXY_PASS
PROXY_HOST_1
PROXY_HOST_2
PROXY_HOST_3
PROXY_HOST_4
PROXY_HOST_5
PROXY_HOST_6
PROXY_HOST_7
PROXY_HOST_8
PROXY_HOST_9
PROXY_HOST_10
PROXY_HOST_11
PROXY_HOST_12
PROXY_PORT
```

### GitHub Variables

proxy 사용 여부 및 시간대는 repository variable로 제어할 수 있습니다.

```text
PROXY_ENABLED=false
TZ=UTC
```

workflow에는 기본값이 `true`로 되어 있으므로, proxy secrets를 등록하지 않은 상태라면 `PROXY_ENABLED=false`를 설정해야 합니다.

## Telegram 명령어

| 명령어 | 설명 |
| --- | --- |
| `/start` | 새 글 알림 구독 시작 |
| `/setinterval [초]` | 새 글 확인 주기 변경, 5~3600초 |
| `/interval` | 현재 새 글 확인 주기 표시 |
| `/setuainterval [횟수]` | User-Agent 변경 주기 변경 |
| `/uainterval` | 현재 User-Agent 변경 주기 표시 |
| `/restart` | 현재 프로세스 재시작 |
| `/help` | 도움말 표시 |

`register_user` 핸들러가 command 메시지를 먼저 받아 chat id를 저장하므로, `/start` 외 명령을 보내도 chat id가 등록됩니다.

## 테스트와 검증

문법 확인:

```bash
python -m py_compile config.py main.py SiteWatcher.py Telegram_bot.py
```

## 주요 파일

| 파일 | 역할 |
| --- | --- |
| `main.py` | 봇 초기화, watcher 등록, Telegram handler 등록 |
| `config.py` | 환경 변수 기반 설정 로드, proxy URL 생성 |
| `Telegram_bot.py` | chat id 관리, watcher 스케줄 실행, Telegram 명령 처리 |
| `SiteWatcher.py` | watcher 공통 HTTP 요청, retry, timeout 처리 |
| `*Watcher.py` | 사이트별 파싱 및 알림 조건 |
| `user_agents.py` | User-Agent 파일 로드 및 로테이션 |
| `Dockerfile` | Docker 이미지 정의 |
| `docker-entrypoint.sh` | `/data/chat_ids.json` 초기화 |

## 운영 메모

- systemd로 기존 봇을 실행 중이면 Docker 컨테이너와 동시에 실행하지 마세요. Telegram polling 충돌이나 중복 알림이 날 수 있습니다.
- `chat_ids.json`은 운영 데이터입니다. Docker에서는 volume을 삭제하면 구독자 목록도 사라집니다.
- `user-agents.txt`는 이미지 빌드 시 복사됩니다. 파일을 바꾸면 이미지를 다시 빌드해야 합니다.
- proxy를 켠 상태에서 필수 proxy 값이 빠지면 시작 시 `RuntimeError`로 종료됩니다.
- 각 watcher는 기본 10초 안에 스크래핑을 끝내지 못하면 해당 회차에서 실패 처리됩니다.

## 라이선스

이 프로젝트는 `LICENSE` 파일의 라이선스를 따릅니다.
