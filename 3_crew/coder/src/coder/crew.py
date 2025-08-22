# -*- coding: utf-8 -*-
# 模組目的：定義 Coder crew 與其代理人/任務的工廠函式。
#
# 注意：本檔案僅加入註解以說明程式碼每一部分的用途；
#      未更動原始程式碼的邏輯或資料結構，以免影響現有行為。

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task


@CrewBase
class Coder():
    """Coder crew

    本類別作為一個「Crew」定義容器，透過裝飾器註冊內部的 agent、task 與 crew
    工廠函式供上層框架使用。
    """

    # 指向 agents 與 tasks 設定檔的路徑（目前以字串表示）。
    # 注意：這裡保留原本的字串設定；若要以字典索引（如 self.agents_config['coder']）
    #       需在外部將 YAML 內容讀入成 dict。此處不修改原程式碼，只補充說明。
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # 一鍵安裝 Docker Desktop 的連結備註（與程式無直接關係，但對 enable_code_execution 有幫助）
    # One click install for Docker Desktop:
    # https://docs.docker.com/desktop/

    @agent
    def coder(self) -> Agent:
        # 這個工廠函式會被框架呼叫以建立一個 Agent 實例。
        # 回傳的 Agent 參數說明：
        # - config: 指定 agent 的設定來源（此處使用 self.agents_config 中的 'coder' 欄位）
        # - verbose: 是否顯示詳細日誌，便於偵錯
        # - allow_code_execution: 是否允許 agent 執行程式碼（風險與安全考量）
        # - code_execution_mode: 程式碼執行的安全模式，本範例為 "safe"（通常代表在隔離環境，例如 Docker 中執行）
        # - max_execution_time: 單次程式碼執行的最長秒數
        # - max_retry_limit: 若失敗時的最大重試次數
        return Agent(
            config=self.agents_config['coder'],
            verbose=True,
            allow_code_execution=True,
            code_execution_mode="safe",  # 使用 Docker 或隔離機制以提升執行安全性
            max_execution_time=30, 
            max_retry_limit=3 
    )


    @task
    def coding_task(self) -> Task:
        # 定義一個 Task 工廠，回傳框架會使用的 Task 物件。
        # config 來源為 tasks_config 中的 'coding_task' 欄位。
        return Task(
            config=self.tasks_config['coding_task'],
        )


    @crew
    def crew(self) -> Crew:
        """Creates the Coder crew

        這個函式建立並回傳一個 Crew 物件，包含要運行的 agents 與 tasks，
        並指定執行程序（例如 sequential、parallel 等）。
        """

        # 回傳的 Crew 參數說明：
        # - agents: 要包含在 crew 中的 agent 清單或映射（由框架透過註冊彙整 self.agents）
        # - tasks: crew 將要執行的 task 清單或映射（由框架透過註冊彙整 self.tasks）
        # - process: 指定執行流程，這裡使用 Process.sequential（依序執行）
        # - verbose: 是否顯示詳細日誌
        return Crew(
            agents=self.agents, 
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
