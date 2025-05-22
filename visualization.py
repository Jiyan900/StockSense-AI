import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

def plot_candlestick_chart(df):
    """
    Create an interactive candlestick chart
    
    Args:
        df (pd.DataFrame): DataFrame with OHLCV data
        
    Returns:
        go.Figure: Plotly figure object
    """
    # Create figure
    fig = go.Figure()
    
    # Add candlestick chart
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Price'
    ))
    
    # Add moving averages if available
    if 'MA20' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['MA20'],
            mode='lines',
            name='20-day MA',
            line=dict(color='yellow', width=1)
        ))
    
    if 'MA50' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['MA50'],
            mode='lines',
            name='50-day MA',
            line=dict(color='orange', width=1)
        ))
    
    # Add Bollinger Bands if available
    if all(col in df.columns for col in ['Upper_Band', 'Lower_Band']):
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['Upper_Band'],
            mode='lines',
            name='Upper Band',
            line=dict(color='rgba(173, 216, 230, 0.5)', width=1)
        ))
        
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['Lower_Band'],
            mode='lines',
            name='Lower Band',
            fill='tonexty',
            fillcolor='rgba(173, 216, 230, 0.1)',
            line=dict(color='rgba(173, 216, 230, 0.5)', width=1)
        ))
    
    # Update layout
    fig.update_layout(
        title='Stock Price Candlestick Chart',
        xaxis_title='Date',
        yaxis_title='Price ($)',
        template='plotly_dark',
        xaxis_rangeslider_visible=False,
        height=500,
    )
    
    # Add range selector
    fig.update_xaxes(
        rangeselector=dict(
            buttons=list([
                dict(count=7, label="1w", step="day", stepmode="backward"),
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=3, label="3m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )
    
    return fig

def plot_historical_trend(df):
    """
    Create a plot of historical price trend
    
    Args:
        df (pd.DataFrame): DataFrame with stock data
        
    Returns:
        go.Figure: Plotly figure object
    """
    # Create figure
    fig = go.Figure()
    
    # Add closing price line
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['Close'],
        mode='lines',
        name='Close Price',
        line=dict(color='#1E88E5', width=2)
    ))
    
    # Add area fill below the line
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['Close'],
        mode='lines',
        name='Close Price',
        line=dict(width=0),
        showlegend=False,
        fill='tozeroy',
        fillcolor='rgba(30, 136, 229, 0.1)'
    ))
    
    # Update layout
    fig.update_layout(
        title='Historical Price Trend',
        xaxis_title='Date',
        yaxis_title='Price ($)',
        template='plotly_dark',
        height=400,
        showlegend=False
    )
    
    return fig

def plot_volume_chart(df):
    """
    Create a chart of trading volume
    
    Args:
        df (pd.DataFrame): DataFrame with stock data
        
    Returns:
        go.Figure: Plotly figure object
    """
    # Create figure
    fig = go.Figure()
    
    # Add volume bars
    colors = ['rgba(0, 255, 0, 0.7)' if row['Close'] >= row['Open'] else 'rgba(255, 0, 0, 0.7)' 
              for _, row in df.iterrows()]
    
    fig.add_trace(go.Bar(
        x=df.index,
        y=df['Volume'],
        name='Volume',
        marker_color=colors
    ))
    
    # Add moving average of volume
    volume_ma = df['Volume'].rolling(window=20).mean()
    fig.add_trace(go.Scatter(
        x=df.index,
        y=volume_ma,
        mode='lines',
        name='20-day MA',
        line=dict(color='yellow', width=2)
    ))
    
    # Update layout
    fig.update_layout(
        title='Trading Volume',
        xaxis_title='Date',
        yaxis_title='Volume',
        template='plotly_dark',
        height=400
    )
    
    return fig

def plot_financial_indicators(df):
    """
    Create a chart with financial indicators
    
    Args:
        df (pd.DataFrame): DataFrame with stock data and indicators
        
    Returns:
        go.Figure: Plotly figure object
    """
    # Create subplots
    fig = make_subplots(rows=3, cols=1, 
                      shared_xaxes=True,
                      vertical_spacing=0.1,
                      subplot_titles=('Price and Moving Averages', 'RSI', 'MACD'),
                      row_heights=[0.5, 0.25, 0.25])
    
    # Add price and moving averages to first subplot
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['Close'],
        mode='lines',
        name='Close Price',
        line=dict(color='#1E88E5', width=2)
    ), row=1, col=1)
    
    if 'MA20' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['MA20'],
            mode='lines',
            name='20-day MA',
            line=dict(color='yellow', width=1)
        ), row=1, col=1)
    
    if 'MA50' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['MA50'],
            mode='lines',
            name='50-day MA',
            line=dict(color='orange', width=1)
        ), row=1, col=1)
    
    # Add RSI to second subplot
    if 'RSI' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['RSI'],
            mode='lines',
            name='RSI',
            line=dict(color='purple', width=1)
        ), row=2, col=1)
        
        # Add overbought/oversold lines
        fig.add_trace(go.Scatter(
            x=df.index,
            y=[70] * len(df),
            mode='lines',
            name='Overbought',
            line=dict(color='red', width=1, dash='dash'),
            showlegend=False
        ), row=2, col=1)
        
        fig.add_trace(go.Scatter(
            x=df.index,
            y=[30] * len(df),
            mode='lines',
            name='Oversold',
            line=dict(color='green', width=1, dash='dash'),
            showlegend=False
        ), row=2, col=1)
    
    # Add MACD to third subplot
    if all(col in df.columns for col in ['MACD', 'Signal_Line']):
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['MACD'],
            mode='lines',
            name='MACD',
            line=dict(color='cyan', width=1)
        ), row=3, col=1)
        
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['Signal_Line'],
            mode='lines',
            name='Signal Line',
            line=dict(color='magenta', width=1)
        ), row=3, col=1)
        
        # Add MACD histogram
        macd_hist = df['MACD'] - df['Signal_Line']
        colors = ['rgba(0, 255, 0, 0.7)' if val >= 0 else 'rgba(255, 0, 0, 0.7)' for val in macd_hist]
        
        fig.add_trace(go.Bar(
            x=df.index,
            y=macd_hist,
            name='MACD Histogram',
            marker_color=colors,
            showlegend=False
        ), row=3, col=1)
    
    # Update layout
    fig.update_layout(
        height=800,
        template='plotly_dark',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Update y-axis titles
    fig.update_yaxes(title_text="Price ($)", row=1, col=1)
    fig.update_yaxes(title_text="RSI", row=2, col=1)
    fig.update_yaxes(title_text="MACD", row=3, col=1)
    
    return fig
