import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import streamlit.web.bootstrap

from enum import Enum, auto

SETTLEMENT_DATE = 'Avräkningsdatum'
ORDER_TIME = 'Order time'

class ResultType(Enum):
    """Enum for different types of analysis results"""
    MATCHING = auto() 
    MATCHING_ORDER_TIME_IN_PERIOD = auto()
    MATCHING_AHEAD = auto()

def get_user_inputs():
    """Get all user inputs from the Streamlit interface"""
    st.title("Transaction Analyst - WGR QLIRO")

    # File uploaders
    st.subheader("Upload Files")
    wgr_file = st.file_uploader("Upload WGR file (CSV)", type=['csv'])
    qliro_file = st.file_uploader("Upload QLIRO file (CSV)", type=['csv'])

    # Date range selector 
    st.subheader("Select Period")
    st.write("Note: each date starts at 00:00:00")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date",
                                value=datetime.now().replace(day=1),
                                format="YYYY-MM-DD")
    with col2:
        # Get last day of current month at end of day
        next_month = datetime.now().replace(day=1) + timedelta(days=32)
        last_day = (next_month.replace(day=1) - timedelta(days=1))
        end_date = st.date_input("End Date",
                              value=last_day.date(),
                              format="YYYY-MM-DD")
    if wgr_file is None or qliro_file is None:
        return None, None, start_date, end_date, None
        
    wgr_df = pd.read_csv(wgr_file, delimiter='\t', encoding='utf-16')
    qliro_df = pd.read_csv(qliro_file, sep=';')
    
    # choose which date to use
    date_column = st.selectbox("Choose date for filtering", [SETTLEMENT_DATE, ORDER_TIME])

    return wgr_df, qliro_df, start_date, end_date, date_column

def process_data(wgr_df, qliro_df, start_date, end_date, date_column):
    """Process the uploaded files and return analysis results"""
    QLIRO_ORDER_ID = 'Butiksordernummer'
    WGR_ORDER_ID = 'Order ID'
    
    try:
        ### WGR ###
        # filter for QLIROCHECKOUT
        wgr_df = wgr_df[wgr_df['Payment method'] == 'QLIROCHECKOUT']
        # filter columns
        wgr_df = wgr_df[[WGR_ORDER_ID, 'Total amount excl. VAT', 'Total VAT','Price excl. VAT', 'Average VAT rate (%)', ORDER_TIME]]

        ### QLIRO ###
        # fix orderIDs
        qliro_df[QLIRO_ORDER_ID] = qliro_df[QLIRO_ORDER_ID].str.replace('WGR', '')

        # filter columns
        qliro_df = qliro_df[[QLIRO_ORDER_ID, 'Belopp','Avräkningsstatus', SETTLEMENT_DATE, 'Transaktionsslutdatum', 'Betalning transaktionsreferens']]

        # merge dfs
        # ensure same types
        wgr_df[WGR_ORDER_ID] = wgr_df[WGR_ORDER_ID].astype(str)
        qliro_df[QLIRO_ORDER_ID] = qliro_df[QLIRO_ORDER_ID].astype(str)

        
        # add total amount excl. VAT and total VAT to qliro_df
        wgr_df['Total Paid WGR'] = wgr_df['Total amount excl. VAT'] + wgr_df['Total VAT']

        # If Total Paid WGR is 0, calculate it from Price excl. VAT and VAT rate
        mask = wgr_df['Total Paid WGR'] == 0
        wgr_df.loc[mask, 'Total Paid WGR'] = wgr_df.loc[mask, 'Price excl. VAT'] * (1 + wgr_df.loc[mask, 'Average VAT rate (%)'] / 100)

        merged_df = pd.merge(
            wgr_df,
            qliro_df, 
            left_on=WGR_ORDER_ID,
            right_on=QLIRO_ORDER_ID,
            how='inner'
        )
        
        # remove QLIROORDERID
        merged_df = merged_df.drop(columns=[QLIRO_ORDER_ID])
        
        # Convert amount columns to numeric type to ensure consistent comparison
        merged_df['Total Paid WGR'] = pd.to_numeric(merged_df['Total Paid WGR'], errors='coerce')
        merged_df['Belopp'] = pd.to_numeric(merged_df['Belopp'], errors='coerce')
        
        
        
        ###### Find mismatches ######
        # Round values to 2 decimal places to avoid floating point comparison issues
        merged_df['Total Paid WGR'] = merged_df['Total Paid WGR'].round(2)
        merged_df['Belopp'] = merged_df['Belopp'].round(2)
        
        # Calculate the difference between WGR and Qliro amounts
        merged_df['Amount Difference'] = (merged_df['Total Paid WGR'] - merged_df['Belopp']).round(2)
        
        # Add a column to flag mismatched amounts, using small threshold for floating point
        merged_df['Amount Mismatch'] = merged_df['Amount Difference'].abs() > 0.01
        
        
        
        
        
        # fix date types
        merged_df['Order time'] = pd.to_datetime(merged_df['Order time'])
        merged_df[SETTLEMENT_DATE] = pd.to_datetime(merged_df[SETTLEMENT_DATE])

        # Convert date inputs to datetime for comparison
        start_datetime = pd.to_datetime(start_date)
        end_datetime = pd.to_datetime(end_date)

        # Debug date filtering
        st.write("Start datetime:", start_datetime)
        st.write("End datetime:", end_datetime)

        # filter for period
        merged_in_period_df = merged_df[(merged_df[date_column] >= start_datetime) & (merged_df[date_column] <= end_datetime)].copy()
        
        # get orders ahead of period
        merged_ahead_df = merged_df[merged_df[date_column] > end_datetime].copy()
        
        results = {}
        results[ResultType.MATCHING] = merged_df
        results[ResultType.MATCHING_ORDER_TIME_IN_PERIOD] = merged_in_period_df
        results[ResultType.MATCHING_AHEAD] = merged_ahead_df
        return results

    except Exception as e:
        st.error(f"Error processing files: {str(e)}")
        return None

def display_df_with_mismatch_highlight(df):
        st.dataframe(
        df.style.apply(
            lambda x: ['background-color: #8B0000' if v else '' for v in df['Amount Mismatch']], 
            axis=0
            )
        )
        # Calculate summary stats on filtered data
        summary_df = df.groupby('Average VAT rate (%)')[[
            'Total Paid WGR',
            'Belopp', 
            'Amount Difference'
        ]].agg({
            'Total Paid WGR': 'sum',
            'Belopp': 'sum',
            'Amount Difference': 'sum'
        }).round(2)
        st.write("Summary by VAT Percentage")
        st.dataframe(summary_df)

def display_results(results, date_column):
    """Display the analysis results in Streamlit"""
    
    st.subheader("Analysis results")
    st.write("The following analysis is shown for orderIDs matching between WGR and QLIRO. Orders where the amount paid does not match the amount invoiced are :red[highlighted in red].")
    # Display the full dataframe with mismatches highlighted in an expandable section
    
    # Display first and last order in matched dataset
    if not results[ResultType.MATCHING].empty:
        st.write("First matched order time:", results[ResultType.MATCHING][date_column].min())
        st.write("Last matched order time:", results[ResultType.MATCHING][date_column].max())

        
    with st.expander("Show all matching orders"):
        display_df_with_mismatch_highlight(results[ResultType.MATCHING])
    
    with st.expander("Orders within selected period"):
        display_df_with_mismatch_highlight(results[ResultType.MATCHING_ORDER_TIME_IN_PERIOD])
    
    with st.expander("Orders ahead of selected period"):
        display_df_with_mismatch_highlight(results[ResultType.MATCHING_AHEAD])
    

def main():
    # Get user inputs
    wgr_df, qliro_df, start_date, end_date, date_column = get_user_inputs()

    # Process data if all inputs are provided
    if all(input is not None for input in [wgr_df, qliro_df, start_date, end_date, date_column]):
        results = process_data(wgr_df, qliro_df, start_date, end_date, date_column)
        if results is not None:
            display_results(results, date_column)
    else:
        st.info("Please upload both files, select a date range, and choose a date column to analyze")

if __name__ == "__main__":
    if "__streamlitmagic__" not in locals():
        import streamlit.web.bootstrap
        streamlit.web.bootstrap.run(__file__, False, [], {})
    main()
