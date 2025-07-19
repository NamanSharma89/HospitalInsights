import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from data_processor import DataProcessor
from visualizations import VisualizationManager
from utils import validate_data, format_number

# Page configuration
st.set_page_config(
    page_title="Hospital Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("🏥 Hospital Data Analytics Dashboard")
    st.markdown("---")
    
    # Initialize session state
    if 'data_processor' not in st.session_state:
        st.session_state.data_processor = None
    if 'patient_data' not in st.session_state:
        st.session_state.patient_data = None
    if 'diagnosis_data' not in st.session_state:
        st.session_state.diagnosis_data = None
    if 'merged_data' not in st.session_state:
        st.session_state.merged_data = None

    # Sidebar for file upload and filters
    with st.sidebar:
        st.header("📁 Data Upload")
        uploaded_file = st.file_uploader(
            "Upload Hospital Excel File",
            type=['xlsx', 'xls'],
            help="Upload an Excel file containing patient_details and diagnosis_details sheets"
        )
        
        if uploaded_file is not None:
            try:
                with st.spinner("Processing uploaded file..."):
                    processor = DataProcessor()
                    patient_data, diagnosis_data, merged_data = processor.process_excel_file(uploaded_file)
                    
                    # Store in session state
                    st.session_state.data_processor = processor
                    st.session_state.patient_data = patient_data
                    st.session_state.diagnosis_data = diagnosis_data
                    st.session_state.merged_data = merged_data
                    
                st.success("✅ Data loaded successfully!")
                
                # Display data summary
                st.subheader("📊 Data Summary")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Patients", len(patient_data))
                with col2:
                    st.metric("Total Diagnoses", len(diagnosis_data))
                
            except Exception as e:
                st.error(f"❌ Error processing file: {str(e)}")
                st.info("Please ensure your Excel file contains 'patient_details' and 'diagnosis_details' sheets with REGISTRY ID columns.")
    
    # Main content area
    if st.session_state.merged_data is not None:
        display_dashboard()
    else:
        display_welcome_message()

def display_welcome_message():
    """Display welcome message when no data is loaded"""
    st.markdown("""
    ## Welcome to the Hospital Analytics Dashboard
    
    This dashboard provides comprehensive analytics for hospital data by joining patient and diagnosis information.
    
    ### Features:
    - 📈 **Patient Demographics**: Age distribution, gender breakdown, and patient statistics
    - 🩺 **Diagnosis Analysis**: Common conditions, trends, and frequency analysis
    - 👤 **Patient Journey**: Individual patient diagnosis history and patterns
    - 🔍 **Cross-Analysis**: Relationships between demographics and diagnosis types
    - 📊 **Interactive Filtering**: Filter by date ranges, departments, and categories
    - 📥 **Export Functionality**: Download reports and visualizations
    
    ### Getting Started:
    1. Upload your Excel file using the sidebar
    2. Ensure your file contains two sheets: `patient_details` and `diagnosis_details`
    3. Both sheets must have a `REGISTRY ID` column for data joining
    4. Explore the interactive dashboard once data is loaded
    
    ### Expected Data Format:
    - **Patient Details Sheet**: Should include patient demographics, registration info
    - **Diagnosis Details Sheet**: Should include diagnosis codes, dates, descriptions
    - **Common Column**: REGISTRY ID (used to link patients with their diagnoses)
    """)

def display_dashboard():
    """Display the main dashboard with all visualizations and metrics"""
    merged_data = st.session_state.merged_data
    patient_data = st.session_state.patient_data
    diagnosis_data = st.session_state.diagnosis_data
    
    # Initialize visualization manager
    viz_manager = VisualizationManager(merged_data, patient_data, diagnosis_data)
    
    # Sidebar filters
    with st.sidebar:
        st.markdown("---")
        st.header("🔍 Filters")
        
        # Date range filter
        if 'DATE' in merged_data.columns or 'DIAGNOSIS_DATE' in merged_data.columns:
            date_col = 'DATE' if 'DATE' in merged_data.columns else 'DIAGNOSIS_DATE'
            try:
                merged_data[date_col] = pd.to_datetime(merged_data[date_col], errors='coerce')
                date_range = st.date_input(
                    "Select Date Range",
                    value=(merged_data[date_col].min(), merged_data[date_col].max()),
                    min_value=merged_data[date_col].min(),
                    max_value=merged_data[date_col].max()
                )
                if len(date_range) == 2:
                    merged_data = merged_data[
                        (merged_data[date_col] >= pd.to_datetime(date_range[0])) & 
                        (merged_data[date_col] <= pd.to_datetime(date_range[1]))
                    ]
            except:
                st.warning("Date filtering not available - invalid date format")
        
        # Gender filter
        if 'GENDER' in merged_data.columns:
            gender_options = ['All'] + list(merged_data['GENDER'].dropna().unique())
            selected_gender = st.selectbox("Gender", gender_options)
            if selected_gender != 'All':
                merged_data = merged_data[merged_data['GENDER'] == selected_gender]
        
        # Age range filter
        if 'AGE' in merged_data.columns:
            age_range = st.slider(
                "Age Range",
                min_value=int(merged_data['AGE'].min()),
                max_value=int(merged_data['AGE'].max()),
                value=(int(merged_data['AGE'].min()), int(merged_data['AGE'].max()))
            )
            merged_data = merged_data[
                (merged_data['AGE'] >= age_range[0]) & 
                (merged_data['AGE'] <= age_range[1])
            ]
        
        # Department filter
        dept_columns = [col for col in merged_data.columns if 'DEPT' in col.upper() or 'DEPARTMENT' in col.upper()]
        if dept_columns:
            dept_col = dept_columns[0]
            dept_options = ['All'] + list(merged_data[dept_col].dropna().unique())
            selected_dept = st.selectbox("Department", dept_options)
            if selected_dept != 'All':
                merged_data = merged_data[merged_data[dept_col] == selected_dept]
    
    # Update visualization manager with filtered data
    viz_manager.update_data(merged_data)
    
    # Key Metrics Row
    st.subheader("📊 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        unique_patients = merged_data['REGISTRY ID'].nunique()
        st.metric("Active Patients", format_number(unique_patients))
    
    with col2:
        total_diagnoses = len(merged_data)
        st.metric("Total Diagnoses", format_number(total_diagnoses))
    
    with col3:
        avg_diagnoses = total_diagnoses / unique_patients if unique_patients > 0 else 0
        st.metric("Avg Diagnoses/Patient", f"{avg_diagnoses:.1f}")
    
    with col4:
        if 'GENDER' in merged_data.columns:
            gender_diversity = merged_data['GENDER'].nunique()
            st.metric("Gender Categories", gender_diversity)
        else:
            st.metric("Data Points", format_number(len(merged_data)))
    
    # Main dashboard tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "👥 Patient Demographics", 
        "🩺 Diagnosis Analysis", 
        "👤 Patient Journey", 
        "🔍 Cross Analysis",
        "📥 Export Data"
    ])
    
    with tab1:
        display_patient_demographics(viz_manager)
    
    with tab2:
        display_diagnosis_analysis(viz_manager)
    
    with tab3:
        display_patient_journey(viz_manager)
    
    with tab4:
        display_cross_analysis(viz_manager)
    
    with tab5:
        display_export_options(merged_data, patient_data, diagnosis_data)

def display_patient_demographics(viz_manager):
    """Display patient demographics visualizations"""
    st.subheader("👥 Patient Demographics Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Age distribution
        age_fig = viz_manager.create_age_distribution()
        if age_fig:
            st.plotly_chart(age_fig, use_container_width=True)
        else:
            st.info("Age data not available for visualization")
    
    with col2:
        # Gender distribution
        gender_fig = viz_manager.create_gender_distribution()
        if gender_fig:
            st.plotly_chart(gender_fig, use_container_width=True)
        else:
            st.info("Gender data not available for visualization")
    
    # Patient registration trends
    st.subheader("📈 Patient Registration Trends")
    registration_fig = viz_manager.create_registration_trends()
    if registration_fig:
        st.plotly_chart(registration_fig, use_container_width=True)
    else:
        st.info("Date information not available for trend analysis")

def display_diagnosis_analysis(viz_manager):
    """Display diagnosis analysis visualizations"""
    st.subheader("🩺 Diagnosis Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top diagnoses
        top_diagnoses_fig = viz_manager.create_top_diagnoses()
        if top_diagnoses_fig:
            st.plotly_chart(top_diagnoses_fig, use_container_width=True)
        else:
            st.info("Diagnosis data not available for analysis")
    
    with col2:
        # Diagnosis frequency over time
        diagnosis_trends_fig = viz_manager.create_diagnosis_trends()
        if diagnosis_trends_fig:
            st.plotly_chart(diagnosis_trends_fig, use_container_width=True)
        else:
            st.info("Time-series diagnosis data not available")
    
    # Diagnosis co-occurrence analysis
    st.subheader("🔗 Diagnosis Co-occurrence Analysis")
    cooccurrence_fig = viz_manager.create_diagnosis_cooccurrence()
    if cooccurrence_fig:
        st.plotly_chart(cooccurrence_fig, use_container_width=True)
    else:
        st.info("Insufficient data for co-occurrence analysis")

def display_patient_journey(viz_manager):
    """Display individual patient journey analysis"""
    st.subheader("👤 Patient Journey Analysis")
    
    merged_data = viz_manager.merged_data
    
    # Patient selector
    patient_ids = sorted(merged_data['REGISTRY ID'].unique())
    selected_patient = st.selectbox(
        "Select Patient (Registry ID)",
        patient_ids,
        help="Choose a patient to view their diagnosis history"
    )
    
    if selected_patient:
        patient_journey_fig = viz_manager.create_patient_journey(selected_patient)
        if patient_journey_fig:
            st.plotly_chart(patient_journey_fig, use_container_width=True)
        
        # Patient details table
        st.subheader(f"📋 Detailed Records for Patient {selected_patient}")
        patient_records = merged_data[merged_data['REGISTRY ID'] == selected_patient]
        st.dataframe(patient_records, use_container_width=True)

def display_cross_analysis(viz_manager):
    """Display cross-analysis between demographics and diagnoses"""
    st.subheader("🔍 Cross Analysis: Demographics vs Diagnoses")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Age vs diagnosis distribution
        age_diagnosis_fig = viz_manager.create_age_diagnosis_analysis()
        if age_diagnosis_fig:
            st.plotly_chart(age_diagnosis_fig, use_container_width=True)
        else:
            st.info("Age and diagnosis data not sufficient for analysis")
    
    with col2:
        # Gender vs diagnosis distribution
        gender_diagnosis_fig = viz_manager.create_gender_diagnosis_analysis()
        if gender_diagnosis_fig:
            st.plotly_chart(gender_diagnosis_fig, use_container_width=True)
        else:
            st.info("Gender and diagnosis data not sufficient for analysis")
    
    # Department analysis if available
    dept_columns = [col for col in viz_manager.merged_data.columns if 'DEPT' in col.upper() or 'DEPARTMENT' in col.upper()]
    if dept_columns:
        st.subheader("🏢 Department Analysis")
        dept_analysis_fig = viz_manager.create_department_analysis()
        if dept_analysis_fig:
            st.plotly_chart(dept_analysis_fig, use_container_width=True)

def display_export_options(merged_data, patient_data, diagnosis_data):
    """Display data export options"""
    st.subheader("📥 Export Data and Reports")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Data Downloads")
        
        # Export merged data
        if st.button("Download Merged Data (CSV)"):
            csv_data = merged_data.to_csv(index=False)
            st.download_button(
                label="📥 Download Merged Data",
                data=csv_data,
                file_name=f"hospital_merged_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        # Export patient data
        if st.button("Download Patient Data (CSV)"):
            csv_data = patient_data.to_csv(index=False)
            st.download_button(
                label="📥 Download Patient Data",
                data=csv_data,
                file_name=f"patient_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        # Export diagnosis data
        if st.button("Download Diagnosis Data (CSV)"):
            csv_data = diagnosis_data.to_csv(index=False)
            st.download_button(
                label="📥 Download Diagnosis Data",
                data=csv_data,
                file_name=f"diagnosis_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col2:
        st.markdown("### 📈 Summary Report")
        
        # Generate summary report
        summary_report = generate_summary_report(merged_data, patient_data, diagnosis_data)
        st.text_area("Summary Report", summary_report, height=300)
        
        if st.button("Download Summary Report"):
            st.download_button(
                label="📥 Download Report",
                data=summary_report,
                file_name=f"hospital_summary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )

def generate_summary_report(merged_data, patient_data, diagnosis_data):
    """Generate a text summary report"""
    report = f"""
HOSPITAL DATA ANALYTICS SUMMARY REPORT
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

OVERVIEW
========
Total Patients: {len(patient_data):,}
Total Diagnoses: {len(diagnosis_data):,}
Merged Records: {len(merged_data):,}
Average Diagnoses per Patient: {len(diagnosis_data) / len(patient_data):.2f}

PATIENT DEMOGRAPHICS
===================
"""
    
    if 'GENDER' in merged_data.columns:
        gender_counts = merged_data.groupby('REGISTRY ID')['GENDER'].first().value_counts()
        report += "Gender Distribution:\n"
        for gender, count in gender_counts.items():
            report += f"  {gender}: {count:,} ({count/len(patient_data)*100:.1f}%)\n"
    
    if 'AGE' in merged_data.columns:
        ages = merged_data.groupby('REGISTRY ID')['AGE'].first()
        report += f"\nAge Statistics:\n"
        report += f"  Average Age: {ages.mean():.1f} years\n"
        report += f"  Age Range: {ages.min():.0f} - {ages.max():.0f} years\n"
    
    # Top diagnoses
    if any('DIAGNOSIS' in col.upper() for col in merged_data.columns):
        diagnosis_cols = [col for col in merged_data.columns if 'DIAGNOSIS' in col.upper()]
        if diagnosis_cols:
            top_diagnoses = merged_data[diagnosis_cols[0]].value_counts().head(10)
            report += f"\nTOP 10 DIAGNOSES\n================\n"
            for i, (diagnosis, count) in enumerate(top_diagnoses.items(), 1):
                report += f"{i:2d}. {diagnosis}: {count:,} cases\n"
    
    report += f"\n\nReport generated by Hospital Analytics Dashboard"
    return report

if __name__ == "__main__":
    main()
