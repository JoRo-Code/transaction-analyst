import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import streamlit.web.bootstrap
from analysis.order_analyzer import OrderAnalyzer

def main():
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

    # Process files when both are uploaded
    if wgr_file and qliro_file and start_date and end_date:
        try:
            analyzer = OrderAnalyzer(wgr_file, qliro_file)
            results = analyzer.analyze(start_date, end_date)
            
            # Display results
            st.subheader("Analysis Results")
            st.dataframe(results['summary'])
            
            st.subheader("Unpaid Orders")
            if not results['unpaid_orders'].empty:
                st.dataframe(results['unpaid_orders'])
            else:
                st.write("No unpaid orders found")
                
            st.subheader("Late Paid Orders")
            if not results['late_paid_orders'].empty:
                st.dataframe(results['late_paid_orders'])
            else:
                st.write("No late paid orders found")
                
        except Exception as e:
            st.error(f"Error processing files: {str(e)}")
    else:
        st.info("Please upload both files and select a date range to analyze")

if __name__ == "__main__":

    if "__streamlitmagic__" not in locals():
        import streamlit.web.bootstrap

        streamlit.web.bootstrap.run(__file__, False, [], {})
    main()
