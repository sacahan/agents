import gradio as gr  # 匯入 Gradio 套件，用於建立網頁介面
from util import css, js, Color  # 匯入自訂樣式、JS 及顏色設定
import pandas as pd  # 匯入 pandas 用於資料處理
from trading_floor import names, lastnames, short_model_names  # 匯入交易員相關資料
import plotly.express as px  # 匯入 plotly 用於繪製圖表
from accounts import Account  # 匯入帳戶物件
from database import read_log  # 匯入日誌讀取函式

# 定義日誌類型對應顏色
mapper = {
    "trace": Color.WHITE,
    "agent": Color.CYAN,
    "function": Color.GREEN,
    "generation": Color.YELLOW,
    "response": Color.MAGENTA,
    "account": Color.RED,
}


# 交易員類別，負責管理個人資料與帳戶
class Trader:
    def __init__(self, name: str, lastname: str, model_name: str):
        self.name = name  # 交易員名字
        self.lastname = lastname  # 交易員姓氏
        self.model_name = model_name  # 使用的模型名稱
        self.account = Account.get(name)  # 取得帳戶物件

    def reload(self):
        # 重新載入帳戶資料
        self.account = Account.get(self.name)

    def get_title(self) -> str:
        # 產生交易員標題 HTML
        return f"<div style='text-align: center;font-size:34px;'>{self.name}<span style='color:#ccc;font-size:24px;'> ({self.model_name}) - {self.lastname}</span></div>"

    def get_strategy(self) -> str:
        # 取得交易策略
        return self.account.get_strategy()

    def get_portfolio_value_df(self) -> pd.DataFrame:
        # 取得投資組合價值的時間序列資料
        df = pd.DataFrame(
            self.account.portfolio_value_time_series, columns=["datetime", "value"]
        )
        df["datetime"] = pd.to_datetime(df["datetime"])
        return df

    def get_portfolio_value_chart(self):
        # 產生投資組合價值折線圖
        df = self.get_portfolio_value_df()
        fig = px.line(df, x="datetime", y="value")
        margin = dict(l=40, r=20, t=20, b=40)
        fig.update_layout(
            height=300,
            margin=margin,
            xaxis_title=None,
            yaxis_title=None,
            paper_bgcolor="#bbb",
            plot_bgcolor="#dde",
        )
        fig.update_xaxes(tickformat="%m/%d", tickangle=45, tickfont=dict(size=8))
        fig.update_yaxes(tickfont=dict(size=8), tickformat=",.0f")
        return fig

    def get_holdings_df(self) -> pd.DataFrame:
        """將持股資料轉為 DataFrame 以便顯示"""
        holdings = self.account.get_holdings()
        if not holdings:
            return pd.DataFrame(columns=["Symbol", "Quantity"])

        df = pd.DataFrame(
            [
                {"Symbol": symbol, "Quantity": quantity}
                for symbol, quantity in holdings.items()
            ]
        )
        return df

    def get_transactions_df(self) -> pd.DataFrame:
        """將交易紀錄轉為 DataFrame 以便顯示"""
        transactions = self.account.list_transactions()
        if not transactions:
            return pd.DataFrame(
                columns=["Timestamp", "Symbol", "Quantity", "Price", "Rationale"]
            )

        return pd.DataFrame(transactions)

    def get_portfolio_value(self) -> str:
        """計算目前投資組合總價值並顯示損益"""
        portfolio_value = self.account.calculate_portfolio_value() or 0.0
        pnl = self.account.calculate_profit_loss(portfolio_value) or 0.0
        color = "green" if pnl >= 0 else "red"
        emoji = "⬆" if pnl >= 0 else "⬇"
        return f"<div style='text-align: center;background-color:{color};'><span style='font-size:32px'>${portfolio_value:,.0f}</span><span style='font-size:24px'>&nbsp;&nbsp;&nbsp;{emoji}&nbsp;${pnl:,.0f}</span></div>"

    def get_logs(self, previous=None) -> str:
        # 取得並格式化日誌資料
        logs = read_log(self.name, last_n=13)
        response = ""
        for log in logs:
            timestamp, type, message = log
            color = mapper.get(type, Color.WHITE).value
            response += f"<span style='color:{color}'>{timestamp} : [{type}] {message}</span><br/>"
        response = f"<div style='height:250px; overflow-y:auto;'>{response}</div>"
        if response != previous:
            return response
        return gr.update()


# 交易員介面類別，負責建立 UI 元件
class TraderView:
    def __init__(self, trader: Trader):
        self.trader = trader
        self.portfolio_value = None
        self.chart = None
        self.holdings_table = None
        self.transactions_table = None

    def make_ui(self):
        # 建立交易員的 UI 介面
        with gr.Column():
            gr.HTML(self.trader.get_title())
            with gr.Row():
                self.portfolio_value = gr.HTML(self.trader.get_portfolio_value)
            with gr.Row():
                self.chart = gr.Plot(
                    self.trader.get_portfolio_value_chart,
                    container=True,
                    show_label=False,
                )
            with gr.Row(variant="panel"):
                self.log = gr.HTML(self.trader.get_logs)
            with gr.Row():
                self.holdings_table = gr.Dataframe(
                    value=self.trader.get_holdings_df,
                    label="Holdings",
                    headers=["Symbol", "Quantity"],
                    row_count=(5, "dynamic"),
                    col_count=2,
                    max_height=300,
                    elem_classes=["dataframe-fix-small"],
                )
            with gr.Row():
                self.transactions_table = gr.Dataframe(
                    value=self.trader.get_transactions_df,
                    label="Recent Transactions",
                    headers=["Timestamp", "Symbol", "Quantity", "Price", "Rationale"],
                    row_count=(5, "dynamic"),
                    col_count=5,
                    max_height=300,
                    elem_classes=["dataframe-fix"],
                )

        # 設定定時器，每 120 秒刷新一次主要資料
        timer = gr.Timer(value=120)
        timer.tick(
            fn=self.refresh,
            inputs=[],
            outputs=[
                self.portfolio_value,
                self.chart,
                self.holdings_table,
                self.transactions_table,
            ],
            show_progress="hidden",
            queue=False,
        )
        # 設定日誌定時器，每 0.5 秒刷新一次日誌
        log_timer = gr.Timer(value=0.5)
        log_timer.tick(
            fn=self.trader.get_logs,
            inputs=[self.log],
            outputs=[self.log],
            show_progress="hidden",
            queue=False,
        )

    def refresh(self):
        # 重新載入交易員資料並回傳各 UI 元件資料
        self.trader.reload()
        return (
            self.trader.get_portfolio_value(),
            self.trader.get_portfolio_value_chart(),
            self.trader.get_holdings_df(),
            self.trader.get_transactions_df(),
        )


# 主介面建構函式
def create_ui():
    """建立交易模擬的主 Gradio 介面"""

    # 建立所有交易員物件與介面
    traders = [
        Trader(trader_name, lastname, model_name)
        for trader_name, lastname, model_name in zip(
            names, lastnames, short_model_names
        )
    ]
    trader_views = [TraderView(trader) for trader in traders]

    # 建立 Gradio Blocks 介面
    with gr.Blocks(
        title="Traders",
        css=css,
        js=js,
        theme=gr.themes.Default(primary_hue="sky"),
        fill_width=True,
    ) as ui:
        with gr.Row():
            for trader_view in trader_views:
                trader_view.make_ui()

    return ui


# 啟動主介面
if __name__ == "__main__":
    ui = create_ui()
    ui.launch(inbrowser=True)
