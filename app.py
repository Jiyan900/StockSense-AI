import streamlit as st
import pandas as pd
import datetime
import time
import os
import matplotlib.pyplot as plt
import fix_database

from stock_data import get_stock_data, get_company_info, get_popular_stocks, search_stocks
from visualization import (
    plot_candlestick_chart, 
    plot_historical_trend, 
    plot_volume_chart, 
    plot_financial_indicators
)
from prediction import predict_stock_trend, calculate_technical_indicators
from export import export_to_excel, export_to_csv, export_to_pdf, get_download_link

# Set page config
st.set_page_config(
    page_title="StockSense AI Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables
if 'selected_stock' not in st.session_state:
    st.session_state.selected_stock = 'AAPL'
if 'date_range' not in st.session_state:
    st.session_state.date_range = 90
if 'prediction_days' not in st.session_state:
    st.session_state.prediction_days = 30

# Make sure database is initialized
fix_database.check_tables()

# Create the exports directory if it doesn't exist
os.makedirs('exports', exist_ok=True)

# Main header
st.title("📊 StockSense AI Analyzer")
st.markdown("*Intelligent stock analysis powered by AI*")

# Sidebar for controls
with st.sidebar:
    st.header("Stock Selection")
    
    # Search functionality
    search_query = st.text_input("Search for a stock symbol or company", "")
    if search_query:
        search_results = search_stocks(search_query)
        if search_results:
            options = {f"{result['symbol']} - {result['name']}": result['symbol'] 
                      for result in search_results}
            selection = st.selectbox("Search Results", options.keys())
            if selection:
                st.session_state.selected_stock = options[selection]
        else:
            st.info("No results found. Try a different search term.")
    
    # Popular stocks selection
    st.subheader("Popular Stocks")
    popular_stocks = get_popular_stocks()
    cols = st.columns(2)
    for i, stock in enumerate(popular_stocks):
        if cols[i % 2].button(f"{stock['symbol']} - {stock['name']}", key=f"btn_{stock['symbol']}"):
            st.session_state.selected_stock = stock['symbol']
    
    # Date range selector
    st.subheader("Settings")
    st.session_state.date_range = st.slider(
        "Historical Data (days)", 
        min_value=30, 
        max_value=365, 
        value=st.session_state.date_range
    )
    
    st.session_state.prediction_days = st.slider(
        "Prediction Horizon (days)", 
        min_value=7, 
        max_value=90, 
        value=st.session_state.prediction_days
    )
    
    # Add refresh button
    if st.button("Refresh Data"):
        st.success("Data refreshed successfully!")
        time.sleep(1)
        st.rerun()

# Calculate date range
end_date = datetime.datetime.now()
start_date = end_date - datetime.timedelta(days=st.session_state.date_range)

# Load data with a spinner to show progress
with st.spinner(f"Loading data for {st.session_state.selected_stock}..."):
    # Get stock data and company info
    df = get_stock_data(st.session_state.selected_stock, start_date, end_date)
    company_info = get_company_info(st.session_state.selected_stock)

# Display basic stock info
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.header(f"{company_info['name']} ({st.session_state.selected_stock})")
    st.markdown(f"**Sector:** {company_info['sector']} | **Industry:** {company_info['industry']}")

with col2:
    latest_price = df['Close'].iloc[-1]
    previous_price = df['Close'].iloc[-2]
    price_change = latest_price - previous_price
    price_change_pct = (price_change / previous_price) * 100
    
    st.metric(
        "Current Price", 
        f"${latest_price:.2f}", 
        f"{price_change:.2f} ({price_change_pct:.2f}%)"
    )

with col3:
    # Get market cap in a readable format
    market_cap = company_info['market_cap']
    if market_cap >= 1e12:
        market_cap_str = f"${market_cap/1e12:.2f}T"
    elif market_cap >= 1e9:
        market_cap_str = f"${market_cap/1e9:.2f}B"
    elif market_cap >= 1e6:
        market_cap_str = f"${market_cap/1e6:.2f}M"
    else:
        market_cap_str = f"${market_cap:.2f}"
    
    st.metric("Market Cap", market_cap_str)

# Add company description
with st.expander("Company Description"):
    st.write(company_info['description'])

# Calculate technical indicators
df = calculate_technical_indicators(df)

# Create tabs for different visualizations
tab1, tab2, tab3 = st.tabs(["📈 Price Charts", "🧠 AI Predictions", "📊 Financial Indicators"])

with tab1:
    # Candlestick chart
    st.subheader("Interactive Candlestick Chart")
    candlestick_fig = plot_candlestick_chart(df)
    st.plotly_chart(candlestick_fig, use_container_width=True)
    
    # Historical trend and volume
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Historical Price Trend")
        trend_fig = plot_historical_trend(df)
        st.plotly_chart(trend_fig, use_container_width=True)
    
    with col2:
        st.subheader("Trading Volume")
        volume_fig = plot_volume_chart(df)
        st.plotly_chart(volume_fig, use_container_width=True)

with tab2:
    st.subheader("AI-Powered Price Prediction")
    
    with st.spinner("Running prediction model..."):
        pred_df, accuracy, confidence = predict_stock_trend(
            df, 
            prediction_days=st.session_state.prediction_days
        )
    
    # Display prediction metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Model Accuracy", f"{accuracy:.2f}%")
    
    with col2:
        st.metric("Confidence Score", f"{confidence:.2f}%")
    
    # Plot prediction chart
    st.subheader(f"Predicted Price Movement (Next {st.session_state.prediction_days} Days)")
    
    # Combine actual and predicted data
    combined_df = pd.concat([
        df[['Close']].rename(columns={'Close': 'Actual'}),
        pred_df[['Predicted']]
    ], axis=1)
    
    # Plot with Plotly
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    # Add actual price line
    fig.add_trace(go.Scatter(
        x=combined_df.index,
        y=combined_df['Actual'],
        mode='lines',
        name='Actual Price',
        line=dict(color='#1E88E5', width=2)
    ))
    
    # Add predicted price line
    fig.add_trace(go.Scatter(
        x=pred_df.index,
        y=pred_df['Predicted'],
        mode='lines',
        name='Predicted Price',
        line=dict(color='#FFD700', width=2, dash='dash')
    ))
    
    # Add confidence interval
    fig.add_trace(go.Scatter(
        x=pred_df.index,
        y=pred_df['Upper_Bound'],
        mode='lines',
        name='Upper Bound',
        line=dict(width=0),
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=pred_df.index,
        y=pred_df['Lower_Bound'],
        mode='lines',
        name='Confidence Interval',
        line=dict(width=0),
        fill='tonexty',
        fillcolor='rgba(255, 215, 0, 0.2)'
    ))
    
    # Update layout
    fig.update_layout(
        title='Stock Price Prediction',
        xaxis_title='Date',
        yaxis_title='Price ($)',
        template='plotly_dark',
        hovermode='x unified',
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Prediction explanation
    st.subheader("Prediction Insights")
    
    last_actual = combined_df['Actual'].iloc[-1]
    last_predicted = pred_df['Predicted'].iloc[-1]
    percent_change = ((last_predicted - last_actual) / last_actual) * 100
    
    if percent_change > 5:
        sentiment = "strongly bullish"
        explanation = "The model predicts significant upward momentum in the stock price."
    elif percent_change > 0:
        sentiment = "moderately bullish"
        explanation = "The model predicts a slight upward trend in the stock price."
    elif percent_change > -5:
        sentiment = "moderately bearish"
        explanation = "The model predicts a slight downward trend in the stock price."
    else:
        sentiment = "strongly bearish"
        explanation = "The model predicts significant downward momentum in the stock price."
    
    st.write(f"The AI prediction model is **{sentiment}** on {st.session_state.selected_stock} for the next {st.session_state.prediction_days} days, with a projected price change of **{percent_change:.2f}%**.")
    st.write(explanation)
    
    st.info("Note: This prediction is based on historical patterns and technical indicators. Always conduct your own research before making investment decisions.")

with tab3:
    st.subheader("Key Financial Indicators")
    
    # Plot financial indicators
    indicators_fig = plot_financial_indicators(df)
    st.plotly_chart(indicators_fig, use_container_width=True)
    
    # Display financial metrics
    st.subheader("Financial Metrics Table")
    
    metrics_data = {
        'Metric': [
            'Close Price', 
            'Trading Volume (Avg.)',
            'Moving Average (20-day)',
            'Moving Average (50-day)',
            'RSI (14-day)',
            'MACD',
            'Bollinger Bands Width',
            'Average True Range',
            '52-Week High',
            '52-Week Low'
        ],
        'Value': [
            f"${df['Close'].iloc[-1]:.2f}",
            f"{df['Volume'].mean():.0f}",
            f"${df['MA20'].iloc[-1]:.2f}",
            f"${df['MA50'].iloc[-1]:.2f}",
            f"{df['RSI'].iloc[-1]:.2f}",
            f"{df['MACD'].iloc[-1]:.4f}",
            f"{(df['Upper_Band'].iloc[-1] - df['Lower_Band'].iloc[-1]) / df['MA20'].iloc[-1]:.4f}",
            f"${df['ATR'].iloc[-1]:.2f}",
            f"${df['Close'].max():.2f}",
            f"${df['Close'].min():.2f}"
        ],
        'Description': [
            'Latest closing price of the stock',
            'Average daily trading volume',
            'Average closing price over the last 20 days',
            'Average closing price over the last 50 days',
            'Relative Strength Index - momentum indicator (>70 overbought, <30 oversold)',
            'Moving Average Convergence Divergence - trend indicator',
            'Measure of price volatility',
            'Average True Range - volatility indicator',
            'Highest price in the past 52 weeks',
            'Lowest price in the past 52 weeks'
        ]
    }
    
    metrics_df = pd.DataFrame(metrics_data)
    st.dataframe(metrics_df, use_container_width=True)

# Add export section
st.markdown("---")
st.subheader("📥 Export Data")
export_col1, export_col2, export_col3 = st.columns(3)

with export_col1:
    if st.button("Export to Excel"):
        with st.spinner("Exporting to Excel..."):
            excel_path = export_to_excel(df, f"{st.session_state.selected_stock}_data.xlsx")
            st.success(f"Data exported to Excel successfully!")
            st.markdown(get_download_link(excel_path, f"{st.session_state.selected_stock} Excel Data"), unsafe_allow_html=True)

with export_col2:
    if st.button("Export to PDF"):
        with st.spinner("Exporting to PDF..."):
            # Use the candlestick chart for the PDF
            pdf_path = export_to_pdf(df, st.session_state.selected_stock, candlestick_fig, f"{st.session_state.selected_stock}_report.pdf")
            st.success(f"Report exported to PDF successfully!")
            st.markdown(get_download_link(pdf_path, f"{st.session_state.selected_stock} PDF Report"), unsafe_allow_html=True)

with export_col3:
    if st.button("Export to CSV"):
        with st.spinner("Exporting to CSV..."):
            csv_path = export_to_csv(df, f"{st.session_state.selected_stock}_data.csv")
            st.success(f"Data exported to CSV successfully!")
            st.markdown(get_download_link(csv_path, f"{st.session_state.selected_stock} CSV Data"), unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("*StockSense AI Analyzer - Built with Streamlit and Python*")
st.caption("Data provided by Yahoo Finance. This application is for informational purposes only and should not be considered financial advice.")
