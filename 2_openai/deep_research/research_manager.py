# 匯入各代理人模組與非同步工具
from agents import (
    Runner,
    trace,
    gen_trace_id,
)  # Runner 用於執行 agent，trace 用於追蹤流程，gen_trace_id 產生追蹤 ID
from search_agent import search_agent  # 搜尋代理人
from planner_agent import (
    planner_agent,
    WebSearchItem,
    WebSearchPlan,
)  # 規劃搜尋任務的代理人與相關資料結構
from writer_agent import writer_agent, ReportData  # 報告撰寫代理人與報告資料結構
from email_agent import email_agent  # Email 寄送代理人
import asyncio  # Python 非同步工具


# 深度研究流程管理類別，負責協調各代理人完成研究、搜尋、報告撰寫與寄送
class ResearchManager:
    async def run(self, query: str):
        """
        執行深度研究主流程，依序：
        1. 建立追蹤 ID 並啟動 trace
        2. 規劃搜尋任務
        3. 執行所有搜尋
        4. 撰寫研究報告
        5. 寄送 email
        6. 以 yield 回報每個階段進度與最終報告內容
        """
        trace_id = gen_trace_id()  # 產生唯一追蹤 ID
        with trace("Research trace", trace_id=trace_id):  # 啟動追蹤區塊
            print(
                f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            )
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"  # 回報 trace 連結
            print("Starting research...")
            search_plan = await self.plan_searches(query)  # 規劃搜尋
            yield "Searches planned, starting to search..."
            search_results = await self.perform_searches(search_plan)  # 執行搜尋
            yield "Searches complete, writing report..."
            report = await self.write_report(query, search_results)  # 撰寫報告
            yield "Report written, sending email..."
            # await self.send_email(report)  # 寄送 email
            yield "Email sent, research complete"
            yield report.markdown_report  # 回傳最終報告內容

    async def plan_searches(self, query: str) -> WebSearchPlan:
        """
        規劃搜尋任務：
        由 planner_agent 根據使用者查詢產生搜尋計畫，回傳 WebSearchPlan
        """
        print("Planning searches...")
        result = await Runner.run(
            planner_agent,
            f"Query: {query}",
        )
        print(
            f"Will perform {len(result.final_output.searches)} searches"
        )  # 顯示即將執行的搜尋數量
        return result.final_output_as(WebSearchPlan)  # 轉換為 WebSearchPlan 型別

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """
        執行所有規劃好的搜尋任務：
        1. 以 asyncio 並行啟動所有搜尋
        2. 逐步收集搜尋結果，並回報進度
        3. 回傳所有搜尋結果
        """
        print("Searching...")
        num_completed = 0  # 已完成搜尋計數
        tasks = [
            asyncio.create_task(self.search(item)) for item in search_plan.searches
        ]  # 建立所有搜尋任務
        results = []
        for task in asyncio.as_completed(tasks):  # 依完成順序收集結果
            result = await task
            if result is not None:
                results.append(result)
            num_completed += 1
            print(f"Searching... {num_completed}/{len(tasks)} completed")  # 顯示進度
        print("Finished searching")
        return results

    async def search(self, item: WebSearchItem) -> str | None:
        """
        執行單一搜尋任務：
        1. 組合搜尋內容與理由
        2. 呼叫 search_agent 執行搜尋
        3. 若成功回傳結果，失敗則回傳 None
        """
        input = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(
                search_agent,
                input,
            )
            return str(result.final_output)
        except Exception:
            return None  # 例外處理，搜尋失敗時回傳 None

    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        """
        撰寫研究報告：
        1. 組合原始查詢與所有搜尋結果
        2. 呼叫 writer_agent 產生報告
        3. 回傳 ReportData 物件
        """
        print("Thinking about report...")
        input = f"Original query: {query}\nSummarized search results: {search_results}"
        result = await Runner.run(
            writer_agent,
            input,
        )

        print("Finished writing report")
        return result.final_output_as(ReportData)

    async def send_email(self, report: ReportData) -> None:
        """
        寄送 email：
        1. 以報告內容呼叫 email_agent 寄送 email
        2. 回報寄送狀態
        """
        print("Writing email...")
        result = await Runner.run(
            email_agent,
            report.markdown_report,
        )
        print("Email sent")
        return report
