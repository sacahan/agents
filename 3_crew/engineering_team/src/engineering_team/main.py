#!/usr/bin/env python
# import sys
import warnings
import os
# from datetime import datetime

from engineering_team.crew import EngineeringTeam

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# 若 output 目錄不存在則建立
os.makedirs('output', exist_ok=True)

# requirements = """
# 一個用於交易模擬平台的簡易帳戶管理系統。
# 系統應允許使用者建立帳戶、存入資金及提領資金。
# 系統應允許使用者記錄買入或賣出股票，並提供數量。
# 系統應計算使用者投資組合的總價值，以及與初始存款的損益。
# 系統應能隨時回報使用者的持股狀況。
# 系統應能隨時回報使用者的損益狀況。
# 系統應能列出使用者歷來的交易紀錄。
# 系統應防止使用者提領導致餘額為負、或購買超過可負擔的股票、或賣出未持有的股票。
# 系統可存取函式 get_share_price(symbol)，該函式回傳股票目前價格，並包含一個測試實作，對 AAPL、TSLA、GOOGL 回傳固定價格。
# """
# module_name = "accounts.py"
# class_name = "Account"

requirements = """
簡介：
將 Markdown 文件轉換為向量並儲存到本地向量資料庫的服務，提供上傳、轉換、檢索與管理功能。

核心 MVP 功能：
1. 文件處理：
    - 支援單一 Markdown 檔案上傳與處理
    - 基本檔案驗證（格式、大小限制）

2. 文件切分：
    - 固定 chunk_size=1000, overlap=200
    - 使用 character-based 切分

3. 向量化：
    - 使用預設模型 "text-embedding-3-small"
    - 將文件片段轉換為向量

4. 向量儲存：
    - 使用 Chroma 作為向量資料庫
    - 基本的儲存與索引功能

5. 基本檢索：
    - 提供語意搜尋功能
    - 支援 top_k 查詢（預設 k=5）
    - 回傳相關片段與來源資訊

6. 簡單管理：
    - 列出已儲存的文件
    - 基本的刪除功能

7. 錯誤處理：
    - 基本異常捕獲與錯誤訊息
    - 簡單的日誌記錄

8. 介面：
    - 使用 Gradio 的 GUI 操作介面
    - 基本的使用範例與說明

預設設定：
- chunk_size=1000, overlap=200
- model="text-embedding-3-small" 
- vector_db="chroma"
- top_k=5

注意：此為 MVP 版本，專注於核心轉換與檢索功能的實現。
"""
module_name = "transformer.py"
class_name = "Transformer"

def run():
    """
    執行 research crew。
    """
    inputs = {
        'requirements': requirements,
        'module_name': module_name,
        'class_name': class_name
    }

    # 建立並執行 crew
    result = EngineeringTeam().crew().kickoff(inputs=inputs)
    print(result)


if __name__ == "__main__":
    run()