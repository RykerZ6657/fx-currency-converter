"""Streamlit interface for the 94692 currency converter assignment."""

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from currency import format_output
from frankfurter import (
    get_currencies_list,
    get_historical_quote,
    get_latest_rates,
    get_rate_trend,
)


st.set_page_config(page_title="FX Converter", page_icon="💱")
st.title("FX Converter")


@st.cache_data(ttl=3600)
def available_currencies() -> list[str] | None:
    """Cache the provider's currency list for one hour."""
    return get_currencies_list()


currencies = available_currencies()
if currencies is None:
    # Do not cache a transient network failure for the full one-hour TTL.
    available_currencies.clear()
    st.error("The currency list could not be loaded. Check your connection and try again.")
    st.stop()

amount = st.number_input(
    "Enter the amount to be converted:", min_value=0.0, value=50.0, step=1.0
)
from_index = currencies.index("AUD") if "AUD" in currencies else 0
to_index = currencies.index("USD") if "USD" in currencies else min(1, len(currencies) - 1)
from_currency = st.selectbox("From Currency:", currencies, index=from_index)
to_currency = st.selectbox("To Currency:", currencies, index=to_index)

if st.button("Get Latest Rate"):
    effective_date, rate = get_latest_rates(from_currency, to_currency, amount)
    if effective_date is None or rate is None:
        st.error("The latest rate could not be loaded. Please try again.")
    else:
        st.subheader("Latest Conversion Rate")
        st.write(format_output(effective_date, from_currency, to_currency, rate, amount))
        trend = get_rate_trend(from_currency, to_currency, 3)
        if trend:
            st.subheader("Rate Trend Over the Last 3 Years")
            chart_data = pd.DataFrame(
                {"Rate": list(trend.values())},
                index=pd.to_datetime(list(trend.keys())),
            )
            st.line_chart(chart_data, x_label="Date", y_label="Rate")
        else:
            st.info("Historical trend data is temporarily unavailable.")

today = date.today()
earliest_date = date(1999, 1, 4)
latest_historical_date = today - timedelta(days=1)
default_date = max(earliest_date, today - timedelta(days=30))
selected_date = st.date_input(
    "Select a date for historical rates:",
    value=default_date,
    min_value=earliest_date,
    max_value=latest_historical_date,
)

if st.button("Conversion Rate"):
    effective_date, rate = get_historical_quote(
        from_currency, to_currency, selected_date.isoformat(), amount
    )
    if effective_date is None or rate is None:
        st.error("The historical rate could not be loaded. Please try another date.")
    else:
        st.subheader("Conversion Rate")
        if effective_date != selected_date.isoformat():
            st.caption(
                f"No rate was published on {selected_date.isoformat()}; "
                f"using the rate from {effective_date}."
            )
        st.write(format_output(effective_date, from_currency, to_currency, rate, amount))
