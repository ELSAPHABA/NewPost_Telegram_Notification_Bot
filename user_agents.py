import random
import sys
import os

def resource_path(relative_path: str) -> str:
    """
    실행 환경(Windows, Linux(x86/ARM), macOS) 및 PyInstaller 환경 모두에서
    데이터 파일 경로를 올바르게 찾도록 보강한 함수.
    - PyInstaller: sys._MEIPASS 내부에서 찾음
    - 일반 실행: 현재 작업 디렉토리 또는 실행 파일 경로에서 탐색
    """

    # 1. PyInstaller 패키징 환경(sys._MEIPASS 존재)
    if hasattr(sys, "_MEIPASS"):
        path = os.path.join(sys._MEIPASS, relative_path)
        if os.path.exists(path):
            return path

    # 2. 실행 파일이 있는 디렉토리 (특히 Windows exe, Linux ELF 환경)
    exe_dir = os.path.dirname(sys.executable)
    path = os.path.join(exe_dir, relative_path)
    if os.path.exists(path):
        return path

    # 3. 현재 작업 디렉토리
    path = os.path.join(os.path.abspath("."), relative_path)
    if os.path.exists(path):
        return path

    # 4. fallback (못 찾으면 기본 상대 경로 그대로 반환 → 에러 발생 유도)
    return relative_path


class UserAgentManager:
    def __init__(self, filepath: str, rotate_interval: int = 20):
        self.filepath = filepath
        self.user_agents = self._load_user_agents()
        self.rotate_interval = rotate_interval
        self.counter = 0
        self.current_user_agent = random.choice(self.user_agents)

    def _load_user_agents(self):
        path = resource_path(self.filepath)
        if not os.path.exists(path):
            raise FileNotFoundError(f"user-agents.txt 파일을 찾을 수 없습니다: {path}")

        with open(path, 'r', encoding='utf-8') as f:
            agents = [line.strip() for line in f if line.strip()]
        if not agents:
            raise RuntimeError("user-agents.txt 파일이 비어있음!")
        return agents

    def get_user_agent(self):
        # 회수 증가, 필요시 rotate
        self.counter += 1
        if self.counter >= self.rotate_interval:
            self.rotate()
            self.counter = 0
        return self.current_user_agent

    def rotate(self):
        # 새로 뽑기 (중복 방지)
        old = self.current_user_agent
        candidates = [ua for ua in self.user_agents if ua != old]
        if not candidates:
            candidates = self.user_agents
        self.current_user_agent = random.choice(candidates)

    def set_interval(self, n: int):
        if not (1 <= n <= 1000):
            raise ValueError("rotate_interval은 1~1000 사이만 허용")
        self.rotate_interval = n

    def get_interval(self):
        return self.rotate_interval

    def reset_counter(self):
        self.counter = 0