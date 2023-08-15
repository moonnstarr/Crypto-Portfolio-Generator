import ccxt
import pandas as pd
import streamlit as st

# STREAMLIT PAGE CONFIGURATION ---------------------------------------------------------------------------------------
st.set_page_config(page_title='Crypto Portfolio', layout='wide')
st.subheader("Cryptocurrency Portfolio Generator")


# CSS Theme customization for sidebar
@st.cache_resource
def page_style():
    with open('style.css') as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


page_style()

col1, col2 = st.columns(2)

with col1:
    # Investment amount text box
    investment = st.number_input("Enter the investment amount")

with col2:
    # Select the exchange
    exchange = st.selectbox("Select your exchange", ['binance', 'kraken'])


def get_top_20_cryptos_details(exchange_name, investment_amount, days=30, limit=20):
    # Create a Binance exchange instance
    exchange = getattr(ccxt, exchange_name)()

    try:
        # Fetch all trading symbols
        symbols = exchange.fetch_tickers().keys()

        # Initialize an empty list to store the top 20 cryptos' details
        top_20_cryptos_details = []

        # Fetch historical OHLCV data for each symbol and calculate price change
        with st.progress(0):
            for idx, symbol in enumerate(symbols):
                try:
                    ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1d',
                                                 since=exchange.milliseconds() - (days * 24 * 60 * 60 * 1000))

                    # Calculate price change
                    if len(ohlcv) >= 2:
                        price_change = ((ohlcv[-1][4] - ohlcv[0][4]) / ohlcv[0][4]) * 100  # Closing price change in %

                        # Fetch additional details
                        ticker = exchange.fetch_ticker(symbol)
                        current_price = ticker['last']
                        trading_volume = ticker['baseVolume']
                        open_24h = ticker['open']
                        high_24h = ticker['high']
                        low_24h = ticker['low']
                        close_24h = ticker['close']

                        # Append details to the list
                        top_20_cryptos_details.append((symbol, price_change, current_price, trading_volume,
                                                       open_24h, high_24h, low_24h, close_24h))
                except (ccxt.BaseError, Exception) as e:
                    # print(f"Error fetching data for {symbol}: {e}")
                    None

                # Update progress bar in Streamlit
                progress_percentage = (idx + 1) / len(symbols)
                progress_percentage = min(progress_percentage, 1.0)  # Ensure the value does not exceed 1.0
                with st.progress(progress_percentage, text="Analyzing the Crypto Market"):
                    pass

        # Sort the list based on price change
        top_20_cryptos_details.sort(key=lambda x: x[1], reverse=True)

        # Get the top 20 cryptocurrencies' details
        top_20_cryptos_details = top_20_cryptos_details[:limit]

        # Convert the list of tuples to a Pandas DataFrame
        columns = ['Symbol', 'Price Change (%)', 'Current Price', 'Trading Volume',
                   'Open 24h', 'High 24h', 'Low 24h', 'Close 24h']
        df = pd.DataFrame(top_20_cryptos_details, columns=columns)
        st.write(df)

        return df
    except (ccxt.BaseError, Exception) as e:
        print(f"Failed to fetch data: {e}")
        return None


def add_investment_portfolio(df):
    # Calculate investment values based on weighted average cost method
    investment_value = investment  # Initial investment value
    df['Weight'] = df['Price Change (%)'] / df['Price Change (%)'].sum()  # Calculate weights
    df['Investment Value'] = df['Weight'] * investment_value
    return df


def print_df_in_streamlit(df):
    df = st.dataframe(df, use_container_width=True, hide_index=True,
                      column_config={
                          'Price Change': st.column_config.NumberColumn(format="%d%%"),
                          'Current Price': st.column_config.NumberColumn(format="$%.4f"),
                          'Open 24h': st.column_config.NumberColumn(format="$%.4f"),
                          'High 24h': st.column_config.NumberColumn(format="$%.4f"),
                          'Low 24h': st.column_config.NumberColumn(format="$%.4f"),
                          'Close 24h': st.column_config.NumberColumn(format="$%.4f"),
                          'Investment Value': st.column_config.NumberColumn(format="$%.4f"),
                          'Weight': st.column_config.NumberColumn(format="%d%%"),
                      })
    return df


def export_to_excel(df, filename="crypto_portfolio.xlsx"):
    df.to_excel(filename, index=False)
    st.success(f"Portfolio exported to {filename}")


if st.button("Generate Portfolio"):
    df = get_top_20_cryptos_details(investment_amount=investment, exchange_name=exchange)
    df = add_investment_portfolio(df)
    print_df_in_streamlit(df)
    # if st.button("Export to Excel"):
    #     export_to_excel(df=df)
else:
    df = get_top_20_cryptos_details(investment_amount=investment, exchange_name=exchange)
    print_df_in_streamlit(df)
