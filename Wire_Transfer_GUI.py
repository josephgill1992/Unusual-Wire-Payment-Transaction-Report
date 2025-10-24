# Import required libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from datetime import datetime

# Set page configuration for Streamlit app
st.set_page_config(page_title="Wire Payment Dashboard", layout="wide")

# Apply light grey background color to the web page
st.markdown("""
    <style>
    .stApp {
        background-color: #f0f0f0;
    }
    </style>
    """, unsafe_allow_html=True)

# Load and process data
@st.cache_data
def load_data():
    """Load and process the data files"""
    # Load SWIFT transaction data from multiple files
    SWIFT = pd.read_csv("SWIFT_csv_20250924_a62566.txt")
    SWIFT_2 = pd.read_csv("SWIFT_csv_2.txt")
    SWIFT_3 = pd.read_csv("SWIFT_csv_3.txt")
    
    # Merge SWIFT data files
    SWIFT_MERGE_1 = pd.concat([SWIFT, SWIFT_2], ignore_index=True)
    SWIFT_MERGE_2 = pd.concat([SWIFT_MERGE_1, SWIFT_3], ignore_index=True)
    
    # Load Wire Transfer KYC data
    WT_KYC = pd.read_csv("Wire Transfer KYC.txt")
    
    # Modify Wire Transfer Limit column
    WT_KYC_2 = WT_KYC.copy()
    WT_KYC_2['Wire Transfer Limit'] = np.where(
        WT_KYC_2['Wire Transfer Limit'] == 500,
        WT_KYC_2['Wire Transfer Limit'] + 5000000.00,
        WT_KYC_2['Wire Transfer Limit']
    )
    
    # Merge KYC data with SWIFT transaction data
    merge_tables = pd.merge(WT_KYC_2, SWIFT_MERGE_2, on='Customer ID', how='left')
    
    # Filter for transactions that exceeded wire transfer limits
    unusual_wp_increase = merge_tables[merge_tables['Outgoing Wire Transfer Amount'] > merge_tables['Wire Transfer Limit']].copy()
    
    return unusual_wp_increase

# Load the dataset
try:
    unusual_wp_increase = load_data()
    
    # Convert 'Date of Transaction' to datetime format for filtering
    unusual_wp_increase['Date of Transaction'] = pd.to_datetime(unusual_wp_increase['Date of Transaction'])
    
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# Main heading for the dashboard
st.markdown("<h1 style='text-align: center;'>Wire Payment Unusual Transaction Report</h1>", unsafe_allow_html=True)

# Create two columns for layout: left sidebar and right content
col1, col2 = st.columns([1, 3])

with col1:
    st.header("Filters")
    
    # Dropdown for Customer Name selection
    customer_names = ['All'] + sorted(unusual_wp_increase['Customer Name_y'].dropna().unique().tolist())
    selected_customer = st.selectbox(
        "Customer Name", 
        options=customer_names,
        help="Select a customer to filter the data"
    )
    

with col2:
    # Filter data based on user selections
    if selected_customer != 'All':
        filtered_data = unusual_wp_increase[
            (unusual_wp_increase['Customer Name_y'] == selected_customer) 
         ]
    else:
        filtered_data = unusual_wp_increase
    
    # Create three tabs for different visualizations
    tab1, tab2, tab3 = st.tabs(["Histogram", "Pie Chart", "Customer Statistics"])
    
    with tab1:
        st.header("Wire Transfer Limits vs Actual Transfers")
        
        # Check if data is available for histogram
        if not filtered_data.empty and selected_customer != 'All':
            # Calculate sums for the histogram
            total_limit = filtered_data['Wire Transfer Limit'].sum()
            total_transfer = filtered_data['Outgoing Wire Transfer Amount'].sum()
            
            # Create histogram
            fig, ax = plt.subplots(figsize=(10, 6))
            categories = ['Wire Transfer Limit', 'Outgoing Wire Amount']
            values = [total_limit, total_transfer]
            colors = ['red', 'blue']
            
            bars = ax.bar(categories, values, color=colors, alpha=0.7)
            ax.set_ylabel('Amount ($)')
            ax.set_title(f'Wire Transfer Comparison for {selected_customer}')
            
            # Add value labels on bars
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'${value:,.2f}', ha='center', va='bottom')
            
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)
            
        else:
            if selected_customer == 'All':
                st.error("Please select a specific customer from the dropdown to view the histogram.")
            else:
                st.warning("No data available for the selected customer and date range.")
    
    with tab2:
        st.header("Outgoing Wire Transfer Distribution")
        
        # Check if data is available for pie chart
        if not filtered_data.empty and selected_customer != 'All':
            # Calculate percentages for pie chart
            filtered_total = filtered_data['Outgoing Wire Transfer Amount'].sum()
            overall_total = unusual_wp_increase['Outgoing Wire Transfer Amount'].sum()
            remaining_total = overall_total - filtered_total
            
            # Create pie chart
            fig, ax = plt.subplots(figsize=(8, 8))
            sizes = [filtered_total, remaining_total]
            labels = [f'Selected: {filtered_total/overall_total*100:.1f}%', 
                     f'Remaining: {remaining_total/overall_total*100:.1f}%']
            colors = ['yellow', 'green']
            
            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax.set_title(f'Outgoing Wire Transfer Distribution\n{selected_customer} vs All Customers')
            st.pyplot(fig)
            
        else:
            if selected_customer == 'All':
                st.error("Please select a specific customer from the dropdown to view the pie chart.")
            else:
                st.warning("No data available for the selected customer and date range.")
    
    with tab3:
        st.header("Customer Appearance Statistics")
        
        # Display customer appearance count
        if selected_customer != 'All':
            customer_count = len(unusual_wp_increase[unusual_wp_increase['Customer Name_y'] == selected_customer])
            st.metric(
                label=f"Number of times {selected_customer} appears in unusual transactions",
                value=customer_count
            )
        else:
            st.info("Select a customer from the dropdown to see their appearance count.")
        
        # Display descriptive statistics table
        st.subheader("Descriptive Statistics of Unusual Transactions")
        st.dataframe(unusual_wp_increase.describe(), use_container_width=True)

# Add some informational text at the bottom
st.sidebar.markdown("---")
st.sidebar.info(
    "This dashboard displays unusual wire payment transactions where "
    "outgoing transfer amounts exceed customer wire transfer limits."
)