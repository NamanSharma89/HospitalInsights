import pandas as pd
import numpy as np
from typing import Tuple, Dict, List
import streamlit as st

class DataProcessor:
    """Handles data processing, validation, and joining operations for hospital data"""
    
    def __init__(self):
        self.patient_data = None
        self.diagnosis_data = None
        self.merged_data = None
        
    def process_excel_file(self, uploaded_file) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Process uploaded Excel file and return patient data, diagnosis data, and merged data
        
        Args:
            uploaded_file: Streamlit uploaded file object
            
        Returns:
            Tuple of (patient_data, diagnosis_data, merged_data)
        """
        try:
            # Read Excel file and get sheet names
            excel_file = pd.ExcelFile(uploaded_file)
            sheet_names = excel_file.sheet_names
            
            # Find patient and diagnosis sheets
            patient_sheet = self._find_sheet(sheet_names, ['patient', 'patients', 'patient_details'])
            diagnosis_sheet = self._find_sheet(sheet_names, ['diagnosis', 'diagnoses', 'diagnosis_details', 'diag'])
            
            if not patient_sheet:
                raise ValueError("Could not find patient data sheet. Expected sheet name containing 'patient' or 'patient_details'")
            
            if not diagnosis_sheet:
                raise ValueError("Could not find diagnosis data sheet. Expected sheet name containing 'diagnosis' or 'diagnosis_details'")
            
            # Read the sheets
            patient_data = pd.read_excel(uploaded_file, sheet_name=patient_sheet)
            diagnosis_data = pd.read_excel(uploaded_file, sheet_name=diagnosis_sheet)
            
            # Clean and validate data
            patient_data = self._clean_dataframe(patient_data)
            diagnosis_data = self._clean_dataframe(diagnosis_data)
            
            # Validate required columns
            patient_data = self._validate_patient_data(patient_data)
            diagnosis_data = self._validate_diagnosis_data(diagnosis_data)
            
            # Merge data on REGISTRY ID
            merged_data = self._merge_data(patient_data, diagnosis_data)
            
            # Store processed data
            self.patient_data = patient_data
            self.diagnosis_data = diagnosis_data
            self.merged_data = merged_data
            
            return patient_data, diagnosis_data, merged_data
            
        except Exception as e:
            raise Exception(f"Error processing Excel file: {str(e)}")
    
    def _find_sheet(self, sheet_names: List[str], keywords: List[str]) -> str:
        """Find sheet name containing any of the specified keywords"""
        for sheet in sheet_names:
            for keyword in keywords:
                if keyword.lower() in sheet.lower():
                    return sheet
        return None
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize dataframe"""
        # Remove completely empty rows and columns
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        # Standardize column names
        df.columns = [str(col).strip().upper() for col in df.columns]
        
        # Handle common registry ID column name variations
        registry_columns = [col for col in df.columns if any(keyword in col.upper() for keyword in ['REGISTRY', 'ID', 'PATIENT_ID', 'PATIENTID'])]
        if registry_columns and 'REGISTRY ID' not in df.columns:
            # Use the first matching column and rename it
            df = df.rename(columns={registry_columns[0]: 'REGISTRY ID'})
        
        return df
    
    def _validate_patient_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and enhance patient data"""
        if 'REGISTRY ID' not in df.columns:
            raise ValueError("Patient data must contain 'REGISTRY ID' column")
        
        # Remove rows with missing registry ID
        df = df.dropna(subset=['REGISTRY ID'])
        
        # Ensure registry ID is string type for consistent joining
        df['REGISTRY ID'] = df['REGISTRY ID'].astype(str)
        
        # Handle common patient data columns
        self._process_age_column(df)
        self._process_gender_column(df)
        self._process_date_columns(df)
        
        return df
    
    def _validate_diagnosis_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and enhance diagnosis data"""
        if 'REGISTRY ID' not in df.columns:
            raise ValueError("Diagnosis data must contain 'REGISTRY ID' column")
        
        # Remove rows with missing registry ID
        df = df.dropna(subset=['REGISTRY ID'])
        
        # Ensure registry ID is string type for consistent joining
        df['REGISTRY ID'] = df['REGISTRY ID'].astype(str)
        
        # Handle common diagnosis data columns
        self._process_date_columns(df)
        self._process_diagnosis_columns(df)
        
        return df
    
    def _process_age_column(self, df: pd.DataFrame):
        """Process and validate age column"""
        # First look for exact 'AGE' column
        if 'AGE' in df.columns:
            age_col = 'AGE'
        else:
            # Look for columns that end with 'AGE' or are exactly 'AGE' to avoid TRIAGE confusion
            age_columns = [col for col in df.columns if col.upper() == 'AGE' or col.upper().endswith(' AGE')]
            if not age_columns:
                # Fallback: look for columns containing 'AGE' but not 'TRIAGE'
                age_columns = [col for col in df.columns if 'AGE' in col.upper() and 'TRIAGE' not in col.upper()]
            
            if age_columns:
                age_col = age_columns[0]
            else:
                return  # No age column found
        
        # Convert to numeric, handle invalid values
        df[age_col] = pd.to_numeric(df[age_col], errors='coerce')
        # Reasonable age range validation
        df.loc[(df[age_col] < 0) | (df[age_col] > 150), age_col] = np.nan
        
        # Debug info to show which column is being used for age
        if age_col != 'AGE':
            st.info(f"Using column '{age_col}' for age data (renamed to 'AGE')")
            df.rename(columns={age_col: 'AGE'}, inplace=True)
        else:
            st.info("Using 'AGE' column for age data")
    
    def _process_gender_column(self, df: pd.DataFrame):
        """Process and standardize gender column"""
        gender_columns = [col for col in df.columns if any(keyword in col.upper() for keyword in ['GENDER', 'SEX'])]
        if gender_columns:
            gender_col = gender_columns[0]
            # Convert to string and handle numeric codes
            df[gender_col] = df[gender_col].astype(str).str.strip()
            
            # Map numeric codes and common variations
            gender_mapping = {
                '1': 'MALE', '1.0': 'MALE',
                '2': 'FEMALE', '2.0': 'FEMALE', 
                '3': 'TRANSGENDER', '3.0': 'TRANSGENDER',
                'M': 'MALE', 'MALE': 'MALE', 'MAN': 'MALE',
                'F': 'FEMALE', 'FEMALE': 'FEMALE', 'WOMAN': 'FEMALE',
                'T': 'TRANSGENDER', 'TRANSGENDER': 'TRANSGENDER', 'TRANS': 'TRANSGENDER',
                'O': 'OTHER', 'OTHER': 'OTHER', 'OTHERS': 'OTHER'
            }
            
            # Apply mapping and convert to uppercase
            df[gender_col] = df[gender_col].str.upper().map(gender_mapping).fillna(df[gender_col].str.upper())
            
            # Debug info to show gender mapping
            unique_values = df[gender_col].value_counts()
            st.info(f"Gender mapping applied. Found: {dict(unique_values)}")
            
            # Rename to standard name
            if gender_col != 'GENDER':
                st.info(f"Using column '{gender_col}' for gender data (renamed to 'GENDER')")
                df.rename(columns={gender_col: 'GENDER'}, inplace=True)
    
    def _process_date_columns(self, df: pd.DataFrame):
        """Process and standardize date columns"""
        date_keywords = ['DATE', 'TIME', 'CREATED', 'UPDATED', 'ADMISSION', 'DISCHARGE']
        date_columns = [col for col in df.columns if any(keyword in col.upper() for keyword in date_keywords)]
        
        for col in date_columns:
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            except:
                continue
    
    def _process_diagnosis_columns(self, df: pd.DataFrame):
        """Process and standardize diagnosis columns"""
        diagnosis_columns = [col for col in df.columns if 'DIAGNOSIS' in col.upper() or 'CONDITION' in col.upper()]
        
        for col in diagnosis_columns:
            # Clean text data
            df[col] = df[col].astype(str).str.strip().str.upper()
            # Remove 'NAN' strings
            df.loc[df[col] == 'NAN', col] = np.nan
    
    def _merge_data(self, patient_data: pd.DataFrame, diagnosis_data: pd.DataFrame) -> pd.DataFrame:
        """Merge patient and diagnosis data on REGISTRY ID"""
        try:
            # Perform left join to keep all diagnoses and match with patient data
            merged_data = diagnosis_data.merge(
                patient_data, 
                on='REGISTRY ID', 
                how='left',
                suffixes=('_DIAG', '_PATIENT')
            )
            
            if merged_data.empty:
                raise ValueError("No matching records found between patient and diagnosis data")
            
            # Report merge statistics
            total_diagnoses = len(diagnosis_data)
            matched_diagnoses = len(merged_data.dropna(subset=[col for col in merged_data.columns if col.endswith('_PATIENT')]))
            
            st.info(f"Merge completed: {matched_diagnoses}/{total_diagnoses} diagnosis records matched with patient data")
            
            return merged_data
            
        except Exception as e:
            raise Exception(f"Error merging data: {str(e)}")
    
    def get_data_summary(self) -> Dict:
        """Get summary statistics of processed data"""
        if self.merged_data is None:
            return {}
        
        summary = {
            'total_patients': self.patient_data['REGISTRY ID'].nunique() if self.patient_data is not None else 0,
            'total_diagnoses': len(self.diagnosis_data) if self.diagnosis_data is not None else 0,
            'merged_records': len(self.merged_data),
            'columns': list(self.merged_data.columns),
            'data_types': self.merged_data.dtypes.to_dict()
        }
        
        return summary
    
    def get_column_info(self) -> Dict:
        """Get information about available columns for visualization"""
        if self.merged_data is None:
            return {}
        
        info = {
            'numeric_columns': list(self.merged_data.select_dtypes(include=[np.number]).columns),
            'categorical_columns': list(self.merged_data.select_dtypes(include=['object']).columns),
            'datetime_columns': list(self.merged_data.select_dtypes(include=['datetime64']).columns),
            'all_columns': list(self.merged_data.columns)
        }
        
        return info
