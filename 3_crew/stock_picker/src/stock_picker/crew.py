from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from pydantic import BaseModel, Field
from typing import List
from .tools.push_tool import PushNotificationTool
from crewai.memory import LongTermMemory, ShortTermMemory, EntityMemory
from crewai.memory.storage.rag_storage import RAGStorage
from crewai.memory.storage.ltm_sqlite_storage import LTMSQLiteStorage

# 定義資料模型：代表一個在新聞或社群中被廣泛討論的公司
class TrendingCompany(BaseModel):
    """代表一間熱門公司的資料模型。

    欄位說明：
    - name: 公司名稱
    - ticker: 股票代號
    - reason: 為何該公司會成為熱門（新聞、事件或其他原因）
    """
    name: str = Field(description="公司名稱")
    ticker: str = Field(description="股票代號")
    reason: str = Field(description="公司成為熱門的原因")


# 定義資料模型：熱門公司清單
class TrendingCompanyList(BaseModel):
    """包含多個 TrendingCompany 的清單模型，用於任務輸出格式化。

    欄位：
    - companies: TrendingCompany 的列表
    """
    companies: List[TrendingCompany] = Field(description="熱門公司清單")


# 定義資料模型：針對單一公司的詳細研究結果
class TrendingCompanyResearch(BaseModel):
    """單一公司詳細研究的資料模型。

    欄位說明：
    - name: 公司名稱
    - market_position: 市場定位與競爭分析摘要
    - future_outlook: 未來展望與成長潛力
    - investment_potential: 投資價值與適合程度評估
    """
    name: str = Field(description="公司名稱")
    market_position: str = Field(description="市場定位與競爭分析")
    future_outlook: str = Field(description="未來展望與成長潛力")
    investment_potential: str = Field(description="投資潛力與適合投資的評估")


# 定義資料模型：多家公司詳細研究的集合
class TrendingCompanyResearchList(BaseModel):
    """包含多個 TrendingCompanyResearch 的清單，用於任務輸出格式化。

    欄位：
    - research_list: TrendingCompanyResearch 的列表
    """
    research_list: List[TrendingCompanyResearch] = Field(description="所有熱門公司之詳細研究清單")


@CrewBase
class StockPicker:
    """StockPicker 的 Crew 類別，組織 Agents、Tasks 與記憶體設定。

    主要職責：
    - 建立並配置多個 Agent（如：尋找熱門公司、財務研究、挑選股票）
    - 定義任務（Task）的輸入與輸出格式
    - 建立 Crew 並注入長期/短期/實體記憶體
    """

    # 設定檔位置（預期為 YAML 檔案）
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def trending_company_finder(self) -> Agent:
        """建立一個用於搜尋或偵測熱門公司的 Agent。

        這個 Agent 使用 SerperDevTool 作為外部工具，並啟用記憶體功能以保留上下文資訊。
        需要記憶功能，避免在多次執行中重複搜尋相同的熱門公司。
        """
        return Agent(config=self.agents_config['trending_company_finder'],
                     tools=[SerperDevTool()], 
                     memory=True)

    @agent
    def financial_researcher(self) -> Agent:
        """建立一個負責財務研究的 Agent。

        使用 SerperDevTool 來取得外部資料或新聞作為研究依據。
        不需要記憶功能，因為每次研究都是獨立的。
        """
        return Agent(config=self.agents_config['financial_researcher'], 
                     tools=[SerperDevTool()])

    @agent
    def stock_picker(self) -> Agent:
        """建立一個用來做最終股票挑選的 Agent，並支援推播通知工具。

        此 Agent 可將結果透過 PushNotificationTool 發送至使用者或系統。
        需要記憶功能，以便在多次執行中保留上下文與結果。
        """
        return Agent(config=self.agents_config['stock_picker'], 
                     tools=[PushNotificationTool()], 
                     memory=True)

    @task
    def find_trending_companies(self) -> Task:
        """定義任務：尋找熱門公司。

        輸出格式透過 output_pydantic 指定為 TrendingCompanyList，方便後續任務使用結構化資料。
        """
        return Task(
            config=self.tasks_config['find_trending_companies'],
            output_pydantic=TrendingCompanyList,
        )

    @task
    def research_trending_companies(self) -> Task:
        """定義任務：對熱門公司進行詳細研究。

        輸出格式為 TrendingCompanyResearchList，以便返回每家公司完整的研究資料。
        """
        return Task(
            config=self.tasks_config['research_trending_companies'],
            output_pydantic=TrendingCompanyResearchList,
        )

    @task
    def pick_best_company(self) -> Task:
        """定義任務：從研究結果中挑選最適合的公司（投資候選）。

        該任務未指定 output_pydantic，代表它可以回傳自由格式或以 config 決定輸出。
        """
        return Task(
            config=self.tasks_config['pick_best_company'],
        )

    @crew
    def crew(self) -> Crew:
        """建立並回傳整個 StockPicker Crew 的實例。

        這裡會設定：
        - manager_agent: 允許任務委派與協調的管理者 Agent
        - process: 使用 hierarchical 的處理流程
        - 記憶體: 啟用長期、短期與實體記憶體以提升上下文能力
        """

        # 建立管理者 Agent（允許委派），由 YAML config 指定參數
        manager = Agent(
            config=self.agents_config["manager"],
            allow_delegation=True,  # 允許使用 hierarchical 進行任務委派
        )

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.hierarchical,
            verbose=True,
            manager_agent=manager,  # agent 控制由哪些 agent 執行 task
            memory=True,
            # 短期記憶：Uses ChromaDB with RAG for current context
            short_term_memory=ShortTermMemory(
                storage=RAGStorage(
                    embedder_config={
                        "provider": "openai",
                        "config": {"model": "text-embedding-3-small"},
                    },
                    type="short_term",
                    path="./memory/",
                )
            ),
            # 長期記憶：Uses SQLite3 to store task results across sessions
            long_term_memory=LongTermMemory(
                storage=LTMSQLiteStorage(db_path="./memory/long_term_memory_storage.db")
            ),
            # 實體記憶：Uses RAG to track entities (people, places, concepts)
            entity_memory=EntityMemory(
                storage=RAGStorage(
                    embedder_config={
                        "provider": "openai",
                        "config": {"model": "text-embedding-3-small"},
                    },
                    type="short_term",
                    path="./memory/",
                )
            ),
        )
