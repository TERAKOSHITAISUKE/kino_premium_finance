# 1分足の取得
import pandas as pd
import numpy as np

import mplfinance as mpf
import streamlit as st
import yfinance as yf

# 一目均衡表の作成関数
def graph(symbol):
    symbol = symbol

    # 基準線作成
    high = symbol['High']
    low = symbol['Low']
    max26 = high.rolling(window=26).max()
    min26 = low.rolling(window=26).min()
    symbol['basic_line'] = ( max26 + min26 ) / 2

    # 転換線作成
    high9 = high.rolling(window=9).max()
    low9 =  low.rolling(window=9).min()
    symbol['turn_line'] = (high9 + low9) / 2

    # 雲（先行スパン1作成）
    symbol['span1'] = (symbol['basic_line'] + symbol['turn_line']) / 2
    symbol['span1'] = symbol['span1'].shift(26)

    # 雲（先行スパン2作成）
    high52 = high.rolling(window=52).max()
    low52 =  low.rolling(window=52).min()
    symbol['span2'] = ( high52 + low52 ) / 2
    symbol['span2'] = symbol['span2'].shift(-26)

    # 遅行線作成
    symbol['slow_line'] = symbol['Adj Close'].shift(-26)

    # mplfinanceを使用し、可視化
    lines = [mpf.make_addplot(symbol['basic_line'], color='#984ea3'), #基準線 紫
            mpf.make_addplot(symbol['turn_line'], color='#ff7f00'),   #転換線 オレンジ
            mpf.make_addplot(symbol['slow_line'], color='#4daf4a'),   #遅行線 緑
           ] 

    fig, ax = mpf.plot(symbol, type='candle', figsize=(16,6), style='classic', xrotation=0, addplot=lines, returnfig=True,
                      fill_between=dict(y1=symbol['span1'].values, y2=symbol['span2'].values, alpha=0.5, color='gray') ) 
    return fig


# シャープレシオ
def sharp_ratio(tickers, start, end=None, g_bonds=0.005, market_profit=0.045):
            
    # データ読み込み
    df = pd.DataFrame()
    for ticker, number in tickers.items():
        df[ticker] = yf.download(number, start, end)['Adj Close']
        
    # 対数利益率を算出
    df_log = np.log(df / df.shift(1))
    # 共分散行列作成
    df_cov = df_log.cov() * 246
    # 個別とマーケットの共分散
    kobetu_cov_market = df_cov.iloc[0, 1]
    # マーケットの分散
    market_var = df_cov.iloc[1, 1]
    # ベータ
    beta = kobetu_cov_market / market_var
    # 期待利益率
    capm = g_bonds + beta * (market_profit - g_bonds)
    # シャープレシオ
    sharpe_ratio = (capm - g_bonds) / (df_log.iloc[:, 0].std() * 246 ** 0.5)
    
    return round(sharpe_ratio, 4)


# 統計情報取得関数
def statistics(symbol):
    # 株価取得
    df = symbol.reset_index()
    
    # 必要カラム作成
    # 陽線1、陰線0
    df["yousen"] = df.apply(lambda x: 1 if (x["Close"] - x["Open"]) >=0 else 0, axis=1)
    # 終値　- 前日終値
    df["close_yclose"] = df["Adj Close"].diff()
    # ＋は1、−は0
    df["close_yclose_win"] = (df['close_yclose'] >= 0).astype(int)
    # 年
    df['year'] = df['Date'].dt.year
    # 四半期
    df['quarter'] = df['Date'].dt.quarter
    # 月
    df['month'] = df['Date'].dt.month
    # 週
    df['week'] = df['Date'].dt.isocalendar().week
    # 曜日(0が月曜日)
    df['dayofweek'] = df['Date'].dt.dayofweek
    # 日
    df['day'] = df['Date'].dt.day
    # 年初から何日目
    df['day_count'] = df['Date'].dt.dayofyear
    
    # カラムリストを取得(年〜)
    targets = df.columns[-7:]
    mokuteki = []

    # 期間ごとの勝率を確認
    for target in targets:
        # トータル日数を取得
        purpose = df.groupby(target).count()[["close_yclose_win"]].rename(columns={"close_yclose_win" : "total_day"})
        # 「前日終値から当日終値で株価」が上昇した日の回数・勝率を取得
        purpose["win_close_close"] = df.groupby(target).sum()["close_yclose_win"]
        purpose["win_close_rate"] = round((purpose["win_close_close"] / purpose["total_day"] * 100), 1).astype("str") + "%"
        # 陽線日の回数・割合を取得
        purpose["win_yousen"] = df.groupby(target).sum()["yousen"]
        purpose["win_yousen_rate"] = round((purpose["win_yousen"] / purpose["total_day"] * 100), 1).astype("str") + "%"
        # 年から日の勝率データフレームを変数mokutekiに格納
        mokuteki.append(purpose.T)
        purpose = pd.DataFrame()
    
    return mokuteki


# 分足取得関数
def minutes(ticker, num):
    try:
        # if文簡素的な記述方法
        return yf.download(ticker, interval = str(num)+"m") if num == 1 else yf.download(ticker, period="60d", interval = str(num)+"m")
    except:
        st.write("エラーが発生しています")