from datetime import datetime, timedelta
import streamlit as st
import plotly.graph_objects as go # type: ignore
from plotly.subplots import make_subplots # type: ignore

def detect_patterns(data):
    """Detect various chart patterns"""
    patterns = {}
    
    # Double Top Detection with strength scoring
    def detect_double_top(prices, tolerance=0.02, max_patterns=5):
        peaks = []
        for i in range(1, len(prices)-1):
            if prices.iloc[i] > prices.iloc[i-1] and prices.iloc[i] > prices.iloc[i+1]:
                peaks.append((i, prices.iloc[i]))
        
        double_tops = []
        for i in range(len(peaks)-1):
            for j in range(i+1, len(peaks)):
                price_diff = abs(peaks[i][1] - peaks[j][1])/peaks[i][1]
                if price_diff < tolerance:
                    # Calculate pattern strength based on price level and formation time
                    strength = (peaks[i][1] + peaks[j][1])/2 * (1 - price_diff)
                    double_tops.append({
                        'start_idx': peaks[i][0],
                        'end_idx': peaks[j][0],
                        'price_level': (peaks[i][1] + peaks[j][1])/2,
                        'strength': strength
                    })
        
        # Sort by strength and return top patterns
        double_tops.sort(key=lambda x: x['strength'], reverse=True)
        return double_tops[:max_patterns]
    
    # Head and Shoulders Detection with strength scoring
    def detect_head_shoulders(prices, tolerance=0.02, max_patterns=5):
        peaks = []
        for i in range(1, len(prices)-1):
            if prices.iloc[i] > prices.iloc[i-1] and prices.iloc[i] > prices.iloc[i+1]:
                peaks.append((i, prices.iloc[i]))
        
        patterns = []
        for i in range(len(peaks)-2):
            if peaks[i+1][1] > peaks[i][1] and peaks[i+1][1] > peaks[i+2][1]:
                shoulder_diff = abs(peaks[i][1] - peaks[i+2][1])/peaks[i][1]
                if shoulder_diff < tolerance:
                    # Calculate pattern strength based on head height and shoulder symmetry
                    head_height = peaks[i+1][1] - (peaks[i][1] + peaks[i+2][1])/2
                    strength = head_height * (1 - shoulder_diff)
                    patterns.append({
                        'left_shoulder': peaks[i],
                        'head': peaks[i+1],
                        'right_shoulder': peaks[i+2],
                        'strength': strength
                    })
        
        # Sort by strength and return top patterns
        patterns.sort(key=lambda x: x['strength'], reverse=True)
        return patterns[:max_patterns]
    
    patterns['double_tops'] = detect_double_top(data['Close'])
    patterns['head_shoulders'] = detect_head_shoulders(data['Close'])
    return patterns

def calculate_key_levels(data, max_levels=3):
    """Calculate support and resistance levels"""
    levels = {
        'support': [],
        'resistance': []
    }
    
    window = 20
    for i in range(window, len(data)):
        if data['Low'].iloc[i] == min(data['Low'].iloc[i-window:i+1]):
            levels['support'].append(data['Low'].iloc[i])
        if data['High'].iloc[i] == max(data['High'].iloc[i-window:i+1]):
            levels['resistance'].append(data['High'].iloc[i])
    
    # Keep only the most significant levels
    levels['support'] = sorted(list(set(levels['support'])))[-max_levels:]
    levels['resistance'] = sorted(list(set(levels['resistance'])))[-max_levels:]
    
    return levels

def plot_patterns(data, patterns):
    """Create interactive plot with detected patterns"""
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, row_heights=[0.7, 0.3])
    
    # Add candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name='Price'
        ),
        row=1, col=1
    )
    
    # Add volume bars
    fig.add_trace(
        go.Bar(
            x=data.index,
            y=data['Volume'],
            name='Volume'
        ),
        row=2, col=1
    )
    
    # Add only the top patterns
    for pattern in patterns['double_tops']:
        fig.add_shape(
            type="line",
            x0=data.index[pattern['start_idx']],
            x1=data.index[pattern['end_idx']],
            y0=pattern['price_level'],
            y1=pattern['price_level'],
            line=dict(
                color="red",
                width=2,
                dash="dash",
            ),
            row=1, col=1
        )
    
    fig.update_layout(
        title='Price Chart with Top Detected Patterns',
        yaxis_title='Price',
        yaxis2_title='Volume',
        xaxis_rangeslider_visible=False
    )
    
    return fig

def implement_pattern_scanner_tab(data):
    st.title("📊 Technical Pattern Analysis")
    
    # Detect patterns
    patterns = detect_patterns(data)
    
    # Display Results
    st.header("Top Detected Patterns")
    
    # Pattern Summary
    st.subheader("Pattern Summary")
    col1, col2 = st.columns(2)
    
    with col1:
        total_patterns = len(patterns['double_tops']) + len(patterns['head_shoulders'])
        st.metric(
            "Significant Patterns Found",
            total_patterns
        )
    
    with col2:
        if total_patterns > 0:
            st.success("Significant patterns detected")
        else:
            st.info("No significant patterns detected")
    
    # Double Tops (showing only top 5)
    st.subheader("Top Double Top Patterns")
    if patterns['double_tops']:
        for idx, pattern in enumerate(patterns['double_tops']):
            st.write(f"Pattern {idx + 1} (Strength: {pattern['strength']:.2f}):")
            st.write(f"- Price Level: ${pattern['price_level']:.2f}")
            st.write(f"- Formation Period: Index {pattern['start_idx']} to {pattern['end_idx']}")
    else:
        st.write("No significant double top patterns detected")
    
    # Head and Shoulders (showing only top 5)
    st.subheader("Top Head and Shoulders Patterns")
    if patterns['head_shoulders']:
        for idx, pattern in enumerate(patterns['head_shoulders']):
            st.write(f"Pattern {idx + 1} (Strength: {pattern['strength']:.2f}):")
            st.write(f"- Head Level: ${pattern['head'][1]:.2f}")
            st.write(f"- Left Shoulder: ${pattern['left_shoulder'][1]:.2f}")
            st.write(f"- Right Shoulder: ${pattern['right_shoulder'][1]:.2f}")
    else:
        st.write("No significant head and shoulders patterns detected")
    
    # Support and Resistance (showing only top 3)
    st.subheader("Key Support and Resistance Levels")
    levels = calculate_key_levels(data)
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("Support Levels:")
        for level in levels['support']:
            st.write(f"${level:.2f}")
    
    with col2:
        st.write("Resistance Levels:")
        for level in levels['resistance']:
            st.write(f"${level:.2f}")
    
    # Plot patterns
    fig = plot_patterns(data, patterns)
    st.plotly_chart(fig, use_container_width=True)

