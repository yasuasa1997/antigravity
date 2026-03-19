import streamlit as st
import pandas as pd
import plotly.express as px
import database
import config
import time
import stock_api

# Page config
st.set_page_config(
    page_title="Stock Price Dashboard",
    page_icon="📈",
    layout="wide"
)

# --- CSS for price flash animations ---
st.markdown("""
<style>
@keyframes flash-red {
    0%   { background-color: rgba(255, 59, 48, 0.0); }
    25%  { background-color: rgba(255, 59, 48, 0.35); }
    50%  { background-color: rgba(255, 59, 48, 0.0); }
    75%  { background-color: rgba(255, 59, 48, 0.35); }
    100% { background-color: rgba(255, 59, 48, 0.0); }
}
@keyframes flash-blue {
    0%   { background-color: rgba(0, 122, 255, 0.0); }
    25%  { background-color: rgba(0, 122, 255, 0.35); }
    50%  { background-color: rgba(0, 122, 255, 0.0); }
    75%  { background-color: rgba(0, 122, 255, 0.35); }
    100% { background-color: rgba(0, 122, 255, 0.0); }
}
.price-card {
    border: 1px solid #333;
    border-radius: 12px;
    padding: 16px 20px;
    text-align: center;
    margin-bottom: 8px;
    transition: transform 0.2s, border-color 0.2s;
    cursor: pointer;
    text-decoration: none;
    display: block;
    color: inherit;
}
.price-card:hover {
    transform: translateY(-4px);
    border-color: #007AFF;
    background-color: rgba(255, 255, 255, 0.05);
}
.price-card .ticker-symbol {
    font-size: 0.85rem;
    color: #888;
    margin-bottom: 2px;
}
.price-card .ticker-name {
    font-size: 1.05rem;
    font-weight: 600;
    margin-bottom: 8px;
}
.price-card .price-value {
    font-size: 1.8rem;
    font-weight: 700;
    margin-bottom: 4px;
}
.price-card .price-delta {
    font-size: 0.95rem;
    font-weight: 500;
}
.price-delta.up {
    color: #FF3B30;
}
.price-delta.down {
    color: #007AFF;
}
.price-delta.flat {
    color: #888;
}
</style>
""", unsafe_allow_html=True)

st.title("📈 Stock Price Dashboard")

# Sidebar
st.sidebar.header("Settings")


# Ticker Management
st.sidebar.subheader("銘柄を追加")

# Search input
search_query = st.sidebar.text_input(
    "会社名 or ティッカーコードで検索",
    key="search_query_input",
    placeholder="例: トヨタ, Sony, 7203.T"
)

# Search button
if st.sidebar.button("🔍 検索"):
    if search_query:
        with st.spinner("検索中..."):
            results = stock_api.search_tickers(search_query)
            if results:
                st.session_state.search_results = results
                st.session_state.search_query_display = search_query
            else:
                st.session_state.search_results = []
                st.session_state.search_query_display = search_query
                st.sidebar.warning("該当する銘柄が見つかりませんでした")

# Display search results if available
if 'search_results' in st.session_state and st.session_state.search_results:
    results = st.session_state.search_results
    query_disp = st.session_state.get('search_query_display', '')
    
    st.sidebar.caption(f"「{query_disp}」の検索結果: {len(results)}件")
    
    # Format options for radio buttons
    options = [f"{r['symbol']}  |  {r['name']}  ({r['exchange']})" for r in results]
    
    selected_idx = st.sidebar.radio(
        "追加する銘柄を選択:",
        range(len(options)),
        format_func=lambda i: options[i],
        key="search_result_radio"
    )
    
    # Add button
    if st.sidebar.button("✅ この銘柄を追加"):
        selected = results[selected_idx]
        with st.spinner(f"{selected['symbol']} のデータを取得中..."):
            data = stock_api.get_ticker_data(selected['symbol'])
            if data:
                if database.add_ticker(data['symbol'], selected['name']):
                    if data['price']:
                        database.insert_price(data['symbol'], data['price'])
                    st.sidebar.success(f"追加しました: {selected['symbol']} ({selected['name']})")
                    # Clear search results
                    del st.session_state.search_results
                    if 'search_query_display' in st.session_state:
                        del st.session_state.search_query_display
                    time.sleep(1)
                    st.rerun()
                else:
                    st.sidebar.error("DBへの追加に失敗しました")
            else:
                st.sidebar.error("株価データの取得に失敗しました")
    
    # Clear search results button
    if st.sidebar.button("❌ 検索結果をクリア"):
        del st.session_state.search_results
        if 'search_query_display' in st.session_state:
            del st.session_state.search_query_display
        st.rerun()

# Get current tickers (list of dicts)
current_ticker_objs = database.get_tickers()
current_symbols = [t['symbol'] for t in current_ticker_objs]
symbol_map = {t['symbol']: t['name'] for t in current_ticker_objs}

def format_ticker(symbol):
    return f"{symbol} ({symbol_map.get(symbol, '')})"

ticker_to_remove = st.sidebar.selectbox(
    "Remove Ticker", 
    [""] + current_symbols, 
    format_func=lambda x: format_ticker(x) if x else ""
)

if st.sidebar.button("Remove"):
    if ticker_to_remove:
        if database.remove_ticker(ticker_to_remove):
            st.sidebar.success(f"Removed {ticker_to_remove}")
            time.sleep(1)
            st.rerun()
        else:
            st.sidebar.error("Failed to remove ticker")

st.sidebar.markdown("---")

auto_refresh = st.sidebar.checkbox("Auto-refresh (15s)", value=False)
selected_tickers = st.sidebar.multiselect(
    "Select Tickers to View",
    current_symbols,
    default=current_symbols,
    format_func=format_ticker
)

# Load data
df = database.get_all_data_df()

if not df.empty:
    # Filter by selected tickers
    df_filtered = df[df['ticker'].isin(selected_tickers)]

    # Display metrics with price change (vs previous close)
    st.subheader("Current Prices")
    cols = st.columns(len(selected_tickers) if len(selected_tickers) > 0 else 1)
    
    # Get latest price per ticker
    latest_prices = df_filtered.sort_values('timestamp').groupby('ticker').tail(1)
    
    # Fetch previous close for each ticker (cached per session to avoid excessive API calls)
    if 'prev_close_cache' not in st.session_state:
        st.session_state.prev_close_cache = {}
    
    for i, ticker in enumerate(selected_tickers):
        ticker_data = latest_prices[latest_prices['ticker'] == ticker]
        
        if not ticker_data.empty:
            current_price = ticker_data.iloc[0]['price']
            
            # Get previous close from cache or API
            if ticker not in st.session_state.prev_close_cache:
                api_data = stock_api.get_ticker_data(ticker)
                if api_data and api_data.get('previousClose'):
                    st.session_state.prev_close_cache[ticker] = api_data['previousClose']
            
            prev_close = st.session_state.prev_close_cache.get(ticker)
            
            # Calculate delta (difference from previous day's close)
            if prev_close is not None and prev_close != 0:
                delta = current_price - prev_close
                delta_pct = (delta / prev_close) * 100
            else:
                delta = 0.0
                delta_pct = 0.0
            
            # Determine flash class and delta display
            if delta > 0:
                flash_class = "flash-up"
                delta_class = "up"
                delta_str = f"+{delta:.2f} ({delta_pct:+.2f}%)"
            elif delta < 0:
                flash_class = "flash-down"
                delta_class = "down"
                delta_str = f"{delta:.2f} ({delta_pct:+.2f}%)"
            else:
                flash_class = ""
                delta_class = "flat"
                delta_str = "±0.00 (0.00%)"
            
            name = symbol_map.get(ticker, '')
            
            # Yahoo Finance Link
            if ticker.endswith('.T'):
                yf_url = f"https://finance.yahoo.co.jp/quote/{ticker}"
            else:
                yf_url = f"https://finance.yahoo.com/quote/{ticker}"
            
            with cols[i % len(cols)]:
                st.markdown(f"""
                <a href="{yf_url}" target="_blank" style="text-decoration: none; color: inherit;">
                    <div class="price-card {flash_class}">
                        <div class="ticker-symbol">{ticker}</div>
                        <div class="ticker-name">{name}</div>
                        <div class="price-value">{current_price:.2f}</div>
                        <div class="price-delta {delta_class}">{delta_str}</div>
                    </div>
                </a>
                """, unsafe_allow_html=True)

    # Display Charts
    st.subheader("Price History")
    
    # Create two columns: Chart and Raw Data
    col1, col2 = st.columns([3, 1])

    with col1:
        if not df_filtered.empty:
            fig = px.line(
                df_filtered, 
                x="timestamp", 
                y="price", 
                color="ticker", 
                title="Stock Prices Over Time",
                markers=True
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for selected tickers.")

    with col2:
        st.subheader("Raw Data")
        st.dataframe(df_filtered.sort_values('timestamp', ascending=False).head(50), use_container_width=True)

else:
    st.info("Waiting for data collector to populate the database...")

# Auto-refresh logic (must be at the end)
if auto_refresh:
    time.sleep(config.INTERVAL_SECONDS)
    st.rerun()
