
# 匯入 Gradio 套件，用於建立網頁介面
import gradio as gr
# 匯入 dotenv 套件，載入 .env 檔案中的環境變數
from dotenv import load_dotenv
# 匯入深度研究流程管理類別
from research_manager import ResearchManager

# 載入 .env 檔案，override=True 代表若有重複變數則以 .env 為主
load_dotenv(override=True)

# 非同步執行深度研究流程，並逐步回報進度
async def run(query: str):
    # 透過 async generator，逐步取得 ResearchManager.run 的回報內容
    async for chunk in ResearchManager().run(query):
        yield chunk  # 將每個階段的進度或結果回傳給 Gradio 介面

# 建立 Gradio 互動式網頁介面
with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    # 顯示標題
    gr.Markdown("# Deep Research")
    # 建立文字輸入框，讓使用者輸入研究主題
    query_textbox = gr.Textbox(label="What topic would you like to research?")
    # 建立執行按鈕
    run_button = gr.Button("Run", variant="primary")
    # 建立 Markdown 區塊，用於顯示研究報告
    report = gr.Markdown(label="Report")
    
    # 當按下執行按鈕時，觸發 run 函式，並將輸入與輸出對應
    run_button.click(fn=run, inputs=query_textbox, outputs=report)
    # 當按下 Enter 時，也觸發 run 函式
    query_textbox.submit(fn=run, inputs=query_textbox, outputs=report)

# 啟動 Gradio 介面，並自動在瀏覽器開啟
ui.launch(inbrowser=True)

