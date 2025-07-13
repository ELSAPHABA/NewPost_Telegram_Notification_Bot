# user_agents.py

import random

class UserAgentManager:
    def __init__(self, filepath, rotate_interval=20):
        self.filepath = filepath
        self.user_agents = self._load_user_agents()
        self.rotate_interval = rotate_interval
        self.counter = 0
        self.current_user_agent = random.choice(self.user_agents)

    def _load_user_agents(self):
        # txt 파일: 한 줄에 하나의 user-agent
        with open(self.filepath, 'r', encoding='utf-8') as f:
            agents = [line.strip() for line in f if line.strip()]
        if not agents:
            raise RuntimeError("user-agent 파일이 비어있음!")
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

    def set_interval(self, n):
        if not (1 <= n <= 1000):
            raise ValueError("rotate_interval은 1~1000 사이만 허용")
        self.rotate_interval = n

    def get_interval(self):
        return self.rotate_interval

    def reset_counter(self):
        self.counter = 0