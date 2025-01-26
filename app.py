import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import streamlit.web.bootstrap

from enum import Enum, auto

class ResultType(Enum):
    """Enum for different types of analysis results"""
    MATCHING = auto() 
    MATCHING_ORDER_TIME_IN_PERIOD = auto()


def get_user_inputs():
    """Get all user inputs from the Streamlit interface"""
    st.title("Transaction Analyst - WGR QLIRO")
    st.write("This app is used to analyze transactions from WGR and QLIRO.")

    # File uploaders
    st.subheader("Upload Files")
    wgr_file = st.file_uploader("Upload WGR file (CSV)", type=['csv'])
    qliro_file = st.file_uploader("Upload QLIRO file (CSV)", type=['csv'])

    # Date range selector 
    st.subheader("Select Period")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date",
                                value=datetime.now().replace(day=1),
                                format="YYYY-MM-DD")
    with col2:
        end_date = st.date_input("End Date",
                              value=datetime.now().replace(day=1) + timedelta(days=32),
                              format="YYYY-MM-DD")
        end_date = end_date.replace(day=1) - timedelta(days=1)  # Last day of month
    
    if wgr_file is None or qliro_file is None:
        return None, None, start_date, end_date
        
    wgr_df = pd.read_csv(wgr_file, delimiter='\t', encoding='utf-16')
    qliro_df = pd.read_csv(qliro_file, sep=';')

    return wgr_df, qliro_df, start_date, end_date

def process_data(wgr_df, qliro_df, start_date, end_date):
    """Process the uploaded files and return analysis results"""
    QLIRO_ORDER_ID = 'Butiksordernummer'
    WGR_ORDER_ID = 'Order ID'
    
    try:
        ### WGR ###
        # filter for QLIROCHECKOUT
        wgr_df = wgr_df[wgr_df['Payment method'] == 'QLIROCHECKOUT']
        # filter columns
        wgr_df = wgr_df[[WGR_ORDER_ID, 'Total amount excl. VAT', 'Total VAT', 'Order time']]

        ### QLIRO ###
        # fix orderIDs
        qliro_df[QLIRO_ORDER_ID] = qliro_df[QLIRO_ORDER_ID].str.replace('WGR', '')

        # filter columns
        qliro_df = qliro_df[[QLIRO_ORDER_ID, 'Belopp','Avräkningsstatus', 'Avräkningsdatum', 'Transaktionsslutdatum', 'Betalning transaktionsreferens']]

        # merge dfs
        # ensure same types
        wgr_df[WGR_ORDER_ID] = wgr_df[WGR_ORDER_ID].astype(str)
        qliro_df[QLIRO_ORDER_ID] = qliro_df[QLIRO_ORDER_ID].astype(str)

        
        # add total amount excl. VAT and total VAT to qliro_df
        wgr_df['Total Paid WGR'] = wgr_df['Total amount excl. VAT'] + wgr_df['Total VAT']

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
        
        # Round values to 2 decimal places to avoid floating point comparison issues
        merged_df['Total Paid WGR'] = merged_df['Total Paid WGR'].round(2)
        merged_df['Belopp'] = merged_df['Belopp'].round(2)
        
        # Calculate the difference between WGR and Qliro amounts
        merged_df['Amount Difference'] = (merged_df['Total Paid WGR'] - merged_df['Belopp']).round(2)
        
        # Add a column to flag mismatched amounts, using small threshold for floating point
        merged_df['Amount Mismatch'] = merged_df['Amount Difference'].abs() > 0.01
        
        # fix date types
        merged_df['Order time'] = pd.to_datetime(merged_df['Order time'])
        merged_df['Avräkningsdatum'] = pd.to_datetime(merged_df['Avräkningsdatum'])

        # Convert date inputs to datetime for comparison
        start_datetime = pd.to_datetime(start_date)
        end_datetime = pd.to_datetime(end_date)

        # filter for period
        merged_in_period_df = merged_df[(merged_df['Order time'] >= start_datetime) & (merged_df['Order time'] <= end_datetime)]

        results ={}
        results[ResultType.MATCHING] = merged_df
        results[ResultType.MATCHING_ORDER_TIME_IN_PERIOD] = merged_in_period_df
        return results

    except Exception as e:
        st.error(f"Error processing files: {str(e)}")
        return None

def display_results(results):
    """Display the analysis results in Streamlit"""
    st.subheader("All matching orders ")
    st.dataframe(
        results[ResultType.MATCHING].style.apply(
            lambda x: ['background-color: #8B0000' if v else '' for v in results[ResultType.MATCHING]['Amount Mismatch']], 
            axis=0
        )
    )
    
    st.subheader("Matching orders within selected period")
    st.dataframe(results[ResultType.MATCHING_ORDER_TIME_IN_PERIOD])
    

def main():
    # Get user inputs
    wgr_df, qliro_df, start_date, end_date = get_user_inputs()

    # Process data if all inputs are provided
    if wgr_df is not None and qliro_df is not None and start_date and end_date:
        results = process_data(wgr_df, qliro_df, start_date, end_date)
        if results is not None:
            display_results(results)
    else:
        st.info("Please upload both files and select a date range to analyze")

if __name__ == "__main__":
    if "__streamlitmagic__" not in locals():
        import streamlit.web.bootstrap
        streamlit.web.bootstrap.run(__file__, False, [], {})
    main()
