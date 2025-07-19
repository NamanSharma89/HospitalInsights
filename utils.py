import pandas as pd
import numpy as np
from typing import Any, List, Dict, Optional
import re

def validate_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate dataframe and return validation results
    
    Args:
        df: DataFrame to validate
        
    Returns:
        Dictionary containing validation results
    """
    validation_results = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'info': {}
    }
    
    # Check if dataframe is empty
    if df.empty:
        validation_results['is_valid'] = False
        validation_results['errors'].append("DataFrame is empty")
        return validation_results
    
    # Check for required columns
    required_columns = ['REGISTRY ID']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        validation_results['is_valid'] = False
        validation_results['errors'].append(f"Missing required columns: {missing_columns}")
    
    # Check for duplicate registry IDs in patient data (if it looks like patient data)
    if 'REGISTRY ID' in df.columns:
        duplicate_ids = df['REGISTRY ID'].duplicated().sum()
        if duplicate_ids > 0:
            # This might be diagnosis data (multiple diagnoses per patient)
            validation_results['warnings'].append(f"Found {duplicate_ids} duplicate Registry IDs (this is normal for diagnosis data)")
    
    # Data quality checks
    validation_results['info']['total_rows'] = len(df)
    validation_results['info']['total_columns'] = len(df.columns)
    validation_results['info']['missing_values'] = df.isnull().sum().sum()
    validation_results['info']['duplicate_rows'] = df.duplicated().sum()
    
    # Check data types
    validation_results['info']['column_types'] = df.dtypes.to_dict()
    
    return validation_results

def format_number(number: int) -> str:
    """
    Format number with appropriate suffixes (K, M, B)
    
    Args:
        number: Number to format
        
    Returns:
        Formatted string
    """
    if number >= 1_000_000_000:
        return f"{number / 1_000_000_000:.1f}B"
    elif number >= 1_000_000:
        return f"{number / 1_000_000:.1f}M"
    elif number >= 1_000:
        return f"{number / 1_000:.1f}K"
    else:
        return str(number)

def clean_text_column(series: pd.Series) -> pd.Series:
    """
    Clean text data in a pandas Series
    
    Args:
        series: Pandas Series containing text data
        
    Returns:
        Cleaned Series
    """
    # Convert to string and handle NaN values
    cleaned = series.astype(str)
    
    # Replace 'nan' strings with actual NaN
    cleaned = cleaned.replace(['nan', 'NaN', 'NULL', 'null', ''], np.nan)
    
    # Strip whitespace and convert to uppercase for consistency
    cleaned = cleaned.str.strip().str.upper()
    
    return cleaned

def detect_date_columns(df: pd.DataFrame) -> List[str]:
    """
    Detect potential date columns in dataframe
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        List of column names that likely contain dates
    """
    date_keywords = ['date', 'time', 'created', 'updated', 'admission', 'discharge', 'birth', 'dob']
    potential_date_columns = []
    
    for col in df.columns:
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in date_keywords):
            potential_date_columns.append(col)
        elif df[col].dtype == 'object':
            # Check if values look like dates
            sample_values = df[col].dropna().head(10)
            date_like_count = 0
            for value in sample_values:
                if isinstance(value, str) and is_date_like(value):
                    date_like_count += 1
            if date_like_count >= len(sample_values) * 0.5:  # 50% threshold
                potential_date_columns.append(col)
    
    return potential_date_columns

def is_date_like(value: str) -> bool:
    """
    Check if a string value looks like a date
    
    Args:
        value: String to check
        
    Returns:
        Boolean indicating if value looks like a date
    """
    date_patterns = [
        r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
        r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
        r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
        r'\d{4}/\d{2}/\d{2}',  # YYYY/MM/DD
    ]
    
    for pattern in date_patterns:
        if re.match(pattern, str(value).strip()):
            return True
    
    return False

def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize column names for consistency
    
    Args:
        df: DataFrame with columns to standardize
        
    Returns:
        DataFrame with standardized column names
    """
    # Create a copy to avoid modifying original
    df_copy = df.copy()
    
    # Convert to uppercase and strip whitespace
    df_copy.columns = [str(col).strip().upper() for col in df_copy.columns]
    
    # Common column name mappings
    column_mappings = {
        'PATIENT_ID': 'REGISTRY ID',
        'PATIENTID': 'REGISTRY ID',
        'ID': 'REGISTRY ID',
        'PATIENT_REGISTRY_ID': 'REGISTRY ID',
        'SEX': 'GENDER',
        'DIAGNOSIS_CODE': 'DIAGNOSIS',
        'DIAG_CODE': 'DIAGNOSIS',
        'CONDITION': 'DIAGNOSIS',
        'DIAGNOSIS_DATE': 'DATE',
        'ADMISSION_DATE': 'DATE',
        'VISIT_DATE': 'DATE'
    }
    
    # Apply mappings
    for old_name, new_name in column_mappings.items():
        if old_name in df_copy.columns and new_name not in df_copy.columns:
            df_copy.rename(columns={old_name: new_name}, inplace=True)
    
    return df_copy

def calculate_age_groups(ages: pd.Series) -> pd.Series:
    """
    Calculate age groups from ages in 10-year chunks
    
    Args:
        ages: Series containing age values
        
    Returns:
        Series with age group labels
    """
    def categorize_age(age):
        if pd.isna(age):
            return 'Unknown'
        age = int(age)
        if age <= 10:
            return '1-10'
        elif age <= 20:
            return '11-20'
        elif age <= 30:
            return '21-30'
        elif age <= 40:
            return '31-40'
        elif age <= 50:
            return '41-50'
        elif age <= 60:
            return '51-60'
        elif age <= 70:
            return '61-70'
        elif age <= 80:
            return '71-80'
        elif age <= 90:
            return '81-90'
        else:
            return '90+'
    
    return ages.apply(categorize_age)

def get_summary_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Get comprehensive summary statistics for a dataframe
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        Dictionary containing summary statistics
    """
    summary = {
        'shape': df.shape,
        'columns': list(df.columns),
        'data_types': df.dtypes.to_dict(),
        'missing_values': df.isnull().sum().to_dict(),
        'missing_percentage': (df.isnull().sum() / len(df) * 100).round(2).to_dict(),
        'duplicate_rows': df.duplicated().sum(),
        'memory_usage': df.memory_usage(deep=True).sum(),
        'numeric_columns': list(df.select_dtypes(include=[np.number]).columns),
        'categorical_columns': list(df.select_dtypes(include=['object']).columns),
        'datetime_columns': list(df.select_dtypes(include=['datetime64']).columns)
    }
    
    # Add numeric statistics for numeric columns
    if summary['numeric_columns']:
        numeric_stats = df[summary['numeric_columns']].describe().to_dict()
        summary['numeric_statistics'] = numeric_stats
    
    # Add unique value counts for categorical columns
    if summary['categorical_columns']:
        categorical_stats = {}
        for col in summary['categorical_columns']:
            categorical_stats[col] = {
                'unique_count': df[col].nunique(),
                'top_values': df[col].value_counts().head().to_dict()
            }
        summary['categorical_statistics'] = categorical_stats
    
    return summary

def export_to_excel(dataframes: Dict[str, pd.DataFrame], filename: str) -> bytes:
    """
    Export multiple dataframes to Excel file
    
    Args:
        dataframes: Dictionary with sheet names as keys and DataFrames as values
        filename: Output filename
        
    Returns:
        Excel file as bytes
    """
    from io import BytesIO
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for sheet_name, df in dataframes.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    output.seek(0)
    return output.getvalue()
