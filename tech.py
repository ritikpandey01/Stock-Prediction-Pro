import logging
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import streamlit as st
import ta  # type: ignore # Technical Analysis library

def cal_enhanced_features(data):
    """Calculate additional technical indicators useful for intraday trading"""
    try:
        # Existing features
        data['Lag1'] = data['Close'].shift(1)
        data['Lag2'] = data['Close'].shift(2)
        data['prev_high'] = data['High'].shift(1)
        data['prev_low'] = data['Low'].shift(1)
        data['prev_open'] = data['Open'].shift(1)
        data['prev_vol'] = data['Volume'].shift(1)
        
        # Moving Averages
        data['ma_5'] = data['Close'].rolling(5).mean()
        data['ma_10'] = data['Close'].rolling(10).mean()
        data['ma_20'] = data['Close'].rolling(20).mean()
        data['ma_50'] = data['Close'].rolling(50).mean()
        data['ema_9'] = ta.trend.ema_indicator(data['Close'], 9)
        
        # Momentum Indicators
        data['RSI'] = ta.momentum.rsi(data['Close'])
        data['MACD'] = ta.trend.macd_diff(data['Close'])
        data['MFI'] = ta.volume.money_flow_index(data['High'], data['Low'], data['Close'], data['Volume'])
        
        # Volatility Indicators
        # Change this line:
        indicator_bb = ta.volatility.BollingerBands(close=data['Close'], window=20, window_dev=2)
    
        # To this:
        bb = ta.volatility.BollingerBands(data['Close'])
        data['BB_upper'] = bb.bollinger_hband()
        data['BB_middle'] = bb.bollinger_mavg()
        data['BB_lower'] = bb.bollinger_lband()        
        
        data['ATR'] = ta.volatility.average_true_range(data['High'], data['Low'], data['Close'])
        
        # Volume Indicators
        data['OBV'] = ta.volume.on_balance_volume(data['Close'], data['Volume'])
        data['Volume_SMA'] = data['Volume'].rolling(window=20).mean()
        
        # Support and Resistance
        data['Pivot'] = (data['High'] + data['Low'] + data['Close']) / 3
        data['R1'] = 2 * data['Pivot'] - data['Low']
        data['S1'] = 2 * data['Pivot'] - data['High']
        
        return data

    except:
        print("Error in calc features")
        raise
    

def get_intraday_signals(data):
    """Generate trading signals based on technical indicators"""
    signals = pd.DataFrame(index=data.index)
    
    # MACD Signal
    signals['MACD_Signal'] = np.where(data['MACD'] > 0, 1, -1)
    
    # RSI Signals
    signals['RSI_Signal'] = np.where(data['RSI'] < 30, 1, np.where(data['RSI'] > 70, -1, 0))
    
    # Bollinger Bands Signals
    signals['BB_Signal'] = np.where(data['Close'] < data['BB_lower'], 1, 
                                  np.where(data['Close'] > data['BB_upper'], -1, 0))
    
    # Volume Signal
    signals['Volume_Signal'] = np.where(data['Volume'] > data['Volume_SMA'] * 1.5, 1, 0)
    
    # Combined Signal
    signals['Combined_Signal'] = (signals['MACD_Signal'] + signals['RSI_Signal'] + 
                                signals['BB_Signal'] + signals['Volume_Signal'])
    
    return signals

def plot_advanced_charts(data):
    """Generate advanced technical analysis charts"""
    figures = {}
    
    # Price and Volume Chart
    fig1, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]})
    ax1.plot(data['Date'], data['Close'], label='Close Price')
    ax1.plot(data['Date'], data['BB_upper'], 'r--', label='BB Upper')
    ax1.plot(data['Date'], data['BB_lower'], 'r--', label='BB Lower')
    ax1.fill_between(data['Date'], data['BB_upper'], data['BB_lower'], alpha=0.1)
    ax1.set_title('Price with Bollinger Bands')
    ax1.legend()
    
    ax2.bar(data['Date'], data['Volume'], label='Volume')
    ax2.plot(data['Date'], data['Volume_SMA'], 'r', label='Volume SMA')
    ax2.set_title('Volume Analysis')
    ax2.legend()
    figures['price_volume'] = fig1
    
    # Technical Indicators Chart
    fig2, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 12))
    ax1.plot(data['Date'], data['RSI'], label='RSI')
    ax1.axhline(y=70, color='r', linestyle='--')
    ax1.axhline(y=30, color='g', linestyle='--')
    ax1.set_title('RSI')
    ax1.legend()
    
    ax2.plot(data['Date'], data['MACD'], label='MACD')
    ax2.axhline(y=0, color='r', linestyle='--')
    ax2.set_title('MACD')
    ax2.legend()
    
    ax3.plot(data['Date'], data['MFI'], label='MFI')
    ax3.axhline(y=80, color='r', linestyle='--')
    ax3.axhline(y=20, color='g', linestyle='--')
    ax3.set_title('Money Flow Index')
    ax3.legend()
    figures['indicators'] = fig2
    
    return figures

    # Add these functions to tech.py
def footer_set():

    st.markdown("""
    <style>
        .footer {
            position: relative;
            top:200px;
            bottom: 0;
            width: 100vw;
            left:-23vw;
            
            background-color: #000000;
            color: white;
            text-align: center;
            padding: 1rem;
            font-family: Arial, sans-serif;
            font-size: 0.9rem;
            box-shadow: 0 -2px 5px rgba(0, 0, 0, 0.2);
        }
        .footer a {
            color: #ff6347;
            text-decoration: none;
        }
        .footer a:hover {
            text-decoration: underline;
        }
    </style>
    <div class='footer'>
        <p style="padding-left: 250px;">📈 Advanced Stock Price Prediction Pro | Made with ❤️ using Streamlit</p>
        <p style="padding-left: 250px;">By <a href="https://www.instagram.com/sb_ritik" target="_blank">Pandey G.</a></p>
    </div>
""", unsafe_allow_html=True)


