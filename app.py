import datetime
import pandas as pd
import streamlit as st
import yfinance as yf
import func

st.title("キノファイナンス")

search = st.sidebar.text_input('【銘柄検索】', '')
stock_code = pd.read_csv("stock_codes.csv").astype('str')
st.sidebar.dataframe(stock_code[(stock_code['銘柄名'].str.contains(search)) | (stock_code['コード'].str.contains(search))], height = 200)

ticker = st.sidebar.text_input("銘柄コードを入力", '^N225')
if ticker.isdigit():
    ticker = ticker + '.T'
else:
    ticker

print(ticker)
#1 期間の取得
start = st.sidebar.date_input("始まり",value= datetime.date(2022, 10, 1), min_value= datetime.date(1970, 1, 1))
end = st.sidebar.date_input("終わり",value=datetime.date.today())

symbol = yf.download(ticker, start, end, rounding=True)

if st.checkbox("株価情報"):
    try:
        purpose = ["株価情報", "チャート", "シャープレシオ"]
        num = st.radio('確認したい情報をチェック', purpose, horizontal=True)

        if num == purpose[0]:
            st.dataframe(symbol, 0, height=200)

        if num == purpose[1]:
            fig = func.graph(symbol)
            st.pyplot(fig)

        if num == purpose[2]:
            tickers = {ticker:ticker, '日経平均':'^N225'}
            g_bonds = st.number_input('国債利回り(%)', 0.1, 0.9, 0.5) / 100 
            market_profit= st.number_input('マーケット利回り（%）', 2.0, 9.0, 4.5) / 100
            sharp = func.sharp_ratio(tickers, start, end, g_bonds, market_profit)
            st.write(f"シャープレシオ(年間)は{sharp}です")
    except:
        st.write('この銘柄情報はありません')

        

if st.checkbox("統計情報"):
    purpose = ["年", "四半期", "月", "週", "曜日", "日", "年初からの経過日数"]
    num = st.radio('過去の統計を確認', purpose, horizontal=True)

    statistics = func.statistics(symbol)
    st.dataframe(statistics[purpose.index(num)])


if st.checkbox("分足csvの取得"):
    mt = [1, 2, 5, 15, 30, 60, 90]
    num = st.selectbox('取得したい分足を選択', mt, index=0)
    kobetu = func.minutes(ticker, num)
    st.dataframe(kobetu)
    csv = kobetu.to_csv(index=False)  
    st.download_button("Download", data=csv, file_name=f"{ticker}_{num}min.csv")


