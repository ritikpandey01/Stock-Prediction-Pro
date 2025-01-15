import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import logging
import datetime
import streamlit as st
from model import get_data, train, model_selection, get_next_day_data, predict, plot_price_analysis, plot_vol_analysis, plot_close_vs_ma, plot_rsi, fetch_current_price,get_current_price
from tech import get_intraday_signals, cal_enhanced_features, plot_advanced_charts,footer_set
from pattern_scanner import implement_pattern_scanner_tab
import ta #type:ignore

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s-%(levelname)s-%(message)s',
    handlers=[
        logging.FileHandler("Stock_Prediction.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Page configuration
st.set_page_config(
    page_title="Stock Price Prediction",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark theme styling (no changes needed)
st.markdown("""
<style>
    
    /* Main theme colors */
    :root {
        --background-color: #0E1117;
        --text-color: #E0E0E0;
        --accent-color: #00FF41;
        --secondary-color: #1E2D3D;
        --hover-color: #2C3E50;
    }
    
    /* Global styles */
    body {
        background-color: var(--background-color);
        color: var(--text-color);
    }
    
    /* Header styling */
    .main h1 {
        color: var(--accent-color);
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #1E2D3D 0%, #0E1117 100%);
        border: 1px solid var(--accent-color);
        border-radius: 5px;
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: var(--secondary-color);
    }
    
    /* Button styling */
    .stButton>button {
        width: 100%;
        background-color: var(--secondary-color);
        color: var(--accent-color);
        border: 1px solid var(--accent-color);
        padding: 0.75rem;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: var(--accent-color);
        color: var(--background-color);
    }
    
    /* Metric containers */
    [data-testid="stMetric"] {
        background-color: var(--secondary-color);
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid var(--accent-color);
    }
    
    [data-testid="stMetricValue"] {
        color: var(--accent-color) !important;
    }
    
    /* Select boxes */
    .stSelectbox {
        background-color: var(--secondary-color);
    }
    
    /* DataFrames */
    .dataframe {
        background-color: var(--secondary-color);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab"] {
        color: var(--accent-color);
    }
    
    .stTabs [data-baseweb="tab-list"] {
        background-color: var(--secondary-color);
        border-radius: 5px;
    }
    
    /* Card styling */
    .card {
        background-color: var(--secondary-color);
        border: 1px solid var(--accent-color);
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# App title
st.markdown("""
    <h1>🔮 Advanced Stock Price Prediction</h1>
""", unsafe_allow_html=True)

# Session state initialization
if 'datasets' not in st.session_state:
    st.session_state['datasets'] = {}
if 'predictions' not in st.session_state:
    st.session_state['predictions'] = {}

# Sidebar
with st.sidebar:
    st.markdown("### Trading Configuration")
    
    # Stock symbol input (simple text input)
    company_symbol = st.text_input("Enter Stock Symbol (e.g., AAPL)", key='symbol')
    
    # Prediction term selection (radio buttons)
    st.markdown("### Time Horizon")
    prediction_term = st.selectbox(
        'Select Prediction Term',
        ['Short Term', 'Mid Term', 'Long Term']
    )
    
    # Time selectors (select boxes instead of sliders)
    if prediction_term == 'Short Term':
        days_to_predict = st.selectbox(
            'Minutes to Predict Ahead',
            options=[1, 2, 5, 15, 30]
        )
        analysis_period = st.selectbox(
            'Historical Data Period To Analyse(Days)',
            options=[1,5]

        )
        
    elif prediction_term == 'Mid Term':
        days_to_predict = st.selectbox(
            'Minutes to Predict Ahead',
            options=[1, 2, 5, 15, 30]
        )
        analysis_period = st.selectbox(
            'Historical Data Period To Analyse(Days)',
            options=[1, 5, 30]

        )
        
    else:
        days_to_predict = st.selectbox(
            'Days to Predict Ahead',
            options=[1, 5]
        )
        analysis_period = st.selectbox(
            'Historical Data Period To Analyse (Months)',
            options=[1, 3, 6,12,24,36]

        )

    # Risk management section
    st.markdown("### Risk Management")
    risk_percentage = st.selectbox(
        "Risk per Trade (%)",
        options=[0.1, 0.5, 1.0, 2.0, 3.0, 4.0, 5.0]
    )
    
    stop_loss = st.selectbox(
        "Stop Loss (%)",
        options=[0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0]
    )

    analyze_button = st.button('🔮 Analyze Stock')

# Main content area
if analyze_button and company_symbol:
    # Progress bar with custom styling
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Configure time period
    if 'Long Term' in prediction_term:
        period = f"{analysis_period}mo"
        interval = f"{days_to_predict}d"
        if analysis_period>6:
            period=f"{int(analysis_period)//12}y"
    else:
        if analysis_period == 30:
            period = "1mo"
        else:
            period = f"{analysis_period}d"
        interval = f"{days_to_predict}m"

    # Fetch and process data
    with st.spinner('🔮 Analyzing market data...'):
        data = get_data(company_symbol, period=period, interval=interval)
        
    if data is not None:
        st.session_state['datasets'][company_symbol] = data
        st.success(f"✅ Analysis complete for {company_symbol}")

        try:
            featured_data=cal_enhanced_features(data)


        except Exception as e:
            st.error(f"❌ Error in analysis: {str(e)}")
            logging.error(f"Feature calculation error: {e}")
            st.stop()
            
    else:
        st.error(f"❌ Failed to fetch data for {company_symbol}")
        st.stop()

    # Create tabs
    tabs = st.tabs([
        "📈 Price Analysis",
        "📊 Technical Indicators",
        "💹 Trading Signals",
        "🔮 Predictions",
        "🔍 Pattern Scanner",
        "📑 Data"
    ])
    
    # Tab 1: Price Analysis
    with tabs[0]:
        st.markdown("## 📈 Price Analysis")
        
        # Market Overview
        current_price = fetch_current_price(company_symbol)
        if current_price is None:
            current_price=get_current_price(company_symbol)
        prev_close = data['Close'].iloc[-2]
        price_change = ((current_price - prev_close) / prev_close) * 100
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Price", f"${current_price:.2f}", 
                     f"{price_change:.2f}%",
                     delta_color="normal")
        with col2:
            st.metric("Day's Range", 
                     f"${data['Low'].iloc[-1]:.2f} - ${data['High'].iloc[-1]:.2f}")
        with col3:
            st.metric("Volume", 
                     f"{data['Volume'].iloc[-1]:,.0f}")

        # Price charts
        col1, col2 = st.columns(2)
        with col1:
            with st.spinner("Loading price chart..."):
                fig = plot_price_analysis(featured_data)
                if fig:
                    st.pyplot(fig)
        with col2:
            with st.spinner("Loading volume analysis..."):
                fig = plot_vol_analysis(featured_data)
                if fig:
                    st.pyplot(fig)
                    
        # Advanced charts
        
        st.markdown("### 📊 Advanced Analysis")
        figures = plot_advanced_charts(featured_data)
            
        col1, col2 = st.columns(2)
        with col1:
            with st.spinner("Loading Price Volume graphs..."):
                st.pyplot(figures['price_volume'])
        with col2:
            with st.spinner("Loading Indicators..."):
                st.pyplot(figures['indicators'])
        
        # Support/Resistance levels
        with st.spinner("Loading Support and Resistance levels"):
            st.markdown("### 🎯 Support and Resistance Levels")
            levels_col1, levels_col2, levels_col3 = st.columns(3)
            with levels_col1:
                st.metric("Resistance 1", f"${featured_data['R1'].iloc[-1]:.2f}")
            with levels_col2:
                st.metric("Pivot Point", f"${featured_data['Pivot'].iloc[-1]:.2f}")
            with levels_col3:
                st.metric("Support 1", f"${featured_data['S1'].iloc[-1]:.2f}")
        footer_set()
        
        
    # Tab 2: Technical Indicators
    with tabs[1]:
        st.markdown("## 📊 Technical Indicators")
        
        # Technical indicator metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("RSI", f"{featured_data['RSI'].iloc[-1]:.2f}")
        with col2:
            st.metric("MACD", f"{featured_data['MACD'].iloc[-1]:.2f}")
        with col3:
            st.metric("MFI", f"{featured_data['MFI'].iloc[-1]:.2f}")
        with col4:
            st.metric("BB Width", f"{(featured_data['BB_upper'].iloc[-1] - featured_data['BB_lower'].iloc[-1]):.2f}")
            
        # Technical charts
        col1, col2 = st.columns(2)
        with col1:
            with st.spinner("Loading moving averages..."):
                fig = plot_close_vs_ma(featured_data)
                if fig:
                    st.pyplot(fig)
        with col2:
            with st.spinner("Loading RSI..."):
                fig = plot_rsi(featured_data)
                if fig:
                    st.pyplot(fig)
        footer_set()

    # Tab 3: Trading Signals
    with tabs[2]:
        st.markdown("## 💹 Trading Signals")
        
        signals = get_intraday_signals(featured_data)
        
        # Market position
        signal_strength = signals['Combined_Signal'].iloc[-1]
        position = "Strong Buy" if signal_strength >= 2 else \
                  "Buy" if signal_strength > 0 else \
                  "Strong Sell" if signal_strength <= -2 else \
                  "Sell" if signal_strength < 0 else "Neutral"
        
        st.markdown(f"### Current Market Position: {position}")
        
        # Trade setup
        st.markdown("### 🎯 Potential Trade Setup")
        stop_loss_price = current_price * (1 - stop_loss / 100)
        risk_amount = current_price * (risk_percentage / 100)
        
        setup_col1, setup_col2, setup_col3 = st.columns(3)
        with setup_col1:
            st.metric("Entry Price", f"${current_price:.2f}")
        with setup_col2:
            st.metric("Stop Loss", f"${stop_loss_price:.2f}")
        with setup_col3:
            st.metric("Risk Amount", f"${risk_amount:.2f}")
        
        # Technical signals
        st.markdown("### 📊 Technical Signals")
        signal_cols = st.columns(4)
        with signal_cols[0]:
            st.metric("MACD", 
                     "Bullish" if signals['MACD_Signal'].iloc[-1] > 0 else "Bearish")
        with signal_cols[1]:
            st.metric("RSI", featured_data['RSI'].iloc[-1].round(2))
        with signal_cols[2]:
            st.metric("MFI", featured_data['MFI'].iloc[-1].round(2))
        with signal_cols[3]:
            st.metric("Volume Trend", 
                     "Above Average" if signals['Volume_Signal'].iloc[-1] > 0 else "Below Average")
        footer_set()

    # Tab 4: Predictions
    with tabs[3]:
        st.markdown("## 🔮 Price Predictions")
        
        with st.spinner("Generating predictions..."):
            try:
                model = train(featured_data)
                if model==None:
                    st.write("Seems Data is not sufficient for Predictions,Please Select Longer Data")
                else:
                    current_data = get_next_day_data(featured_data)
                    prediction = predict(model, current_data)

                    if prediction:
                        st.session_state['predictions'][company_symbol] = prediction
                        
                        # Prediction metrics
                        st.markdown("### 📊 Prediction Results")
                        pred_col1, pred_col2, pred_col3 = st.columns(3)
                        
                        with pred_col1:
                            st.metric(
                                "Current Price",
                                f"${current_price:.2f}",
                                f"{price_change:.2f}%"
                            )
                        
                        price_change_pred = ((prediction - current_price) / current_price) * 100
                        with pred_col2:
                            st.metric(
                                f"Predicted Price ({days_to_predict} {'min' if 'Short' in prediction_term else 'hr' if 'Mid' in prediction_term else 'day'}{'s' if days_to_predict > 1 else ''} ahead)",
                                f"${prediction:.2f}",
                                f"{price_change_pred:.2f}%"
                            )
                        
                        with pred_col3:
                            avg_pred = (prediction + current_price) / 2
                            st.metric(
                                "Average Predicted Price",
                                f"${avg_pred:.2f}"
                            )
                        
                        # Prediction visualization
                        st.markdown("### 📈 Price Prediction Visualization")
                        try:
                            with st.spinner("Generating prediction chart..."):
                                fig, ax = plt.subplots(figsize=(12, 6))
                                
                                # Historical prices
                                ax.plot(data['Date'], data['Close'], 
                                    label='Historical', color='#1f77b4', linewidth=2)
                                
                                # Predicted price
                                if 'Short' in prediction_term:
                                    future_date = data['Date'].iloc[-1] + pd.Timedelta(minutes=days_to_predict)
                                elif 'Mid' in prediction_term:
                                    future_date = data['Date'].iloc[-1] + pd.Timedelta(hours=days_to_predict)
                                else:
                                    future_date = data['Date'].iloc[-1] + pd.Timedelta(days=days_to_predict)
                                
                                ax.plot([data['Date'].iloc[-1], future_date], 
                                    [data['Close'].iloc[-1], prediction],
                                    label='Predicted', color='#ff7f0e', 
                                    linewidth=2, linestyle='--')
                                
                                # Styling
                                ax.set_title(f'{company_symbol} Price Prediction', fontsize=14)
                                ax.set_xlabel('Date', fontsize=12)
                                ax.set_ylabel('Price ($)', fontsize=12)
                                ax.grid(True, alpha=0.3)
                                ax.legend()
                                
                                # Add confidence interval
                                confidence = 0.95
                                std_dev = data['Close'].std()
                                margin = std_dev * 1.96  # 95% confidence interval
                                
                                ax.fill_between([data['Date'].iloc[-1], future_date],
                                            [data['Close'].iloc[-1] - margin, prediction - margin],
                                            [data['Close'].iloc[-1] + margin, prediction + margin],
                                            color='gray', alpha=0.2, label='Confidence Interval')
                                
                                st.pyplot(fig)
                                
                                # Prediction insights
                                st.markdown("### 🎯 Prediction Insights")
                                insight_col1, insight_col2 = st.columns(2)
                                
                                with insight_col1:
                                    st.markdown("""
                                    #### Technical Factors
                                    - RSI: {} ({})
                                    - MACD: {} ({})
                                    - Volume Trend: {}
                                    """.format(
                                        round(featured_data['RSI'].iloc[-1], 2),
                                        "Overbought" if featured_data['RSI'].iloc[-1] > 70 else "Oversold" if featured_data['RSI'].iloc[-1] < 30 else "Neutral",
                                        round(featured_data['MACD'].iloc[-1], 2),
                                        "Bullish" if featured_data['MACD'].iloc[-1] > 0 else "Bearish",
                                        "Above Average" if featured_data['Volume'].iloc[-1] > featured_data['Volume'].mean() else "Below Average"
                                    ))
                                
                                with insight_col2:
                                    st.markdown("""
                                    #### Price Targets
                                    - Resistance: ${:.2f}
                                    - Support: ${:.2f}
                                    - Pivot: ${:.2f}
                                    """.format(
                                        featured_data['R1'].iloc[-1],
                                        featured_data['S1'].iloc[-1],
                                        featured_data['Pivot'].iloc[-1]
                                    ))
                                
                                st.warning("⚠️ Note: These predictions are based on historical data and technical analysis. Always conduct thorough research before making investment decisions.")
                                
                        except Exception as e:
                            st.error(f"Error generating prediction visualization: {str(e)}")
                            logging.error(f"Prediction visualization error: {e}")
                    
                    else:
                        st.error("Unable to generate price prediction")
            
            except Exception as e:
                st.error(f"Error in prediction generation: {str(e)}")
                logging.error(f"Prediction generation error: {e}")
        footer_set()

    # Tab 5: Pattern Scanner
    with tabs[4]:
        implement_pattern_scanner_tab(featured_data)
        footer_set()
        
    # Tab 6: Data & Analysis
    with tabs[5]:
        st.markdown("## 📑 Data & Analysis")
        
        # Data overview
        st.markdown("### 📊 Data Overview")
        
        # Summary statistics
        st.markdown("#### Summary Statistics")
        summary_stats = featured_data[['Open', 'High', 'Low', 'Close', 'Volume']].describe()
        st.dataframe(summary_stats.style.format("{:.2f}"))
        
        # Raw data with technical indicators
        st.markdown("#### Raw Data with Technical Indicators")
        st.dataframe(
            featured_data[['Open', 'High', 'Low', 'Close', 'Volume',
                           'RSI', 'MACD', 'BB_middle', 'OBV', 'Pivot']
                         ].style.format("{:.2f}")
        )
        
        # Performance metrics
        st.markdown("### 📈 Performance Metrics")
        perf_col1, perf_col2, perf_col3 = st.columns(3)
        
        with perf_col1:
            returns = featured_data['Close'].pct_change()
            volatility = returns.std() * np.sqrt(252)  # Annualized volatility
            st.metric("Volatility (Annualized)", f"{volatility:.2%}")
        
        with perf_col2:
            sharpe_ratio = (returns.mean() * 252) / (returns.std() * np.sqrt(252))
            st.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")
        
        with perf_col3:
            max_drawdown = (featured_data['Close'] / featured_data['Close'].cummax() - 1).min()
            st.metric("Maximum Drawdown", f"{max_drawdown:.2%}")
        
        # Export data option
        st.markdown("### 💾 Export Data")
        if st.button("Download Analysis Data"):
            csv = featured_data.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"{company_symbol}_analysis.csv",
                mime="text/csv"
            )
        footer_set()
    # Cleanup
    progress_bar.empty()
    status_text.empty()
