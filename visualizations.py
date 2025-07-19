import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List, Dict

class VisualizationManager:
    """Manages all visualization components for the hospital dashboard"""
    
    def __init__(self, merged_data: pd.DataFrame, patient_data: pd.DataFrame, diagnosis_data: pd.DataFrame):
        self.merged_data = merged_data
        self.patient_data = patient_data
        self.diagnosis_data = diagnosis_data
        
    def update_data(self, merged_data: pd.DataFrame):
        """Update the merged data for visualizations"""
        self.merged_data = merged_data
    
    def create_age_distribution(self) -> Optional[go.Figure]:
        """Create age distribution histogram with age categories"""
        if 'AGE' not in self.merged_data.columns:
            return None
        
        # Get unique patients with their ages
        patient_ages = self.merged_data.groupby('REGISTRY ID')['AGE'].first().dropna()
        
        if patient_ages.empty:
            return None
        
        # Create age categories
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
        
        # Apply categorization
        age_categories = patient_ages.apply(categorize_age)
        age_counts = age_categories.value_counts()
        
        # Define proper order for categories
        category_order = ['1-10', '11-20', '21-30', '31-40', '41-50', 
                         '51-60', '61-70', '71-80', '81-90', '90+', 'Unknown']
        
        # Reindex to ensure proper ordering
        age_counts = age_counts.reindex(category_order).fillna(0)
        
        fig = px.bar(
            x=age_counts.index,
            y=age_counts.values,
            title="Patient Age Distribution by Category",
            labels={'x': 'Age Group', 'y': 'Number of Patients'},
            color=age_counts.values,
            color_continuous_scale='Blues'
        )
        
        fig.update_layout(
            showlegend=False,
            height=400,
            xaxis_title="Age Group",
            yaxis_title="Number of Patients"
        )
        
        return fig
    
    def create_gender_distribution(self) -> Optional[go.Figure]:
        """Create gender distribution pie chart"""
        if 'GENDER' not in self.merged_data.columns:
            return None
        
        # Get unique patients with their gender
        patient_genders = self.merged_data.groupby('REGISTRY ID')['GENDER'].first().dropna()
        
        if patient_genders.empty:
            return None
        
        gender_counts = patient_genders.value_counts()
        
        fig = px.pie(
            values=gender_counts.values,
            names=gender_counts.index,
            title="Patient Gender Distribution",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig.update_layout(height=400)
        return fig
    
    def create_registration_trends(self) -> Optional[go.Figure]:
        """Create patient registration trends over time"""
        date_columns = [col for col in self.merged_data.columns if 'DATE' in col.upper() and 'DIAGNOSIS' not in col.upper()]
        
        if not date_columns:
            return None
        
        date_col = date_columns[0]
        
        try:
            # Get unique patients with registration dates
            patient_dates = self.merged_data.groupby('REGISTRY ID')[date_col].first().dropna()
            
            if patient_dates.empty:
                return None
            
            # Group by month for trend analysis
            monthly_registrations = patient_dates.groupby(patient_dates.dt.to_period('M')).size()
            
            fig = px.line(
                x=monthly_registrations.index.astype(str),
                y=monthly_registrations.values,
                title="Patient Registration Trends",
                labels={'x': 'Month', 'y': 'New Registrations'}
            )
            
            fig.update_layout(
                height=400,
                xaxis_title="Month",
                yaxis_title="New Registrations"
            )
            
            return fig
        except:
            return None
    
    def create_top_diagnoses(self) -> Optional[go.Figure]:
        """Create top diagnoses bar chart"""
        diagnosis_columns = [col for col in self.merged_data.columns if 'DIAGNOSIS' in col.upper()]
        
        if not diagnosis_columns:
            return None
        
        diagnosis_col = diagnosis_columns[0]
        diagnosis_counts = self.merged_data[diagnosis_col].value_counts().head(15)
        
        if diagnosis_counts.empty:
            return None
        
        fig = px.bar(
            x=diagnosis_counts.values,
            y=diagnosis_counts.index,
            orientation='h',
            title="Top 15 Most Common Diagnoses",
            labels={'x': 'Number of Cases', 'y': 'Diagnosis'},
            color=diagnosis_counts.values,
            color_continuous_scale='Blues'
        )
        
        fig.update_layout(
            height=600,
            showlegend=False,
            yaxis={'categoryorder': 'total ascending'}
        )
        
        return fig
    
    def create_diagnosis_trends(self) -> Optional[go.Figure]:
        """Create diagnosis trends over time"""
        diagnosis_date_columns = [col for col in self.merged_data.columns if 'DATE' in col.upper() and 'DIAGNOSIS' in col.upper()]
        
        if not diagnosis_date_columns:
            # Try general date columns
            date_columns = [col for col in self.merged_data.columns if 'DATE' in col.upper()]
            if not date_columns:
                return None
            diagnosis_date_columns = date_columns
        
        date_col = diagnosis_date_columns[0]
        
        try:
            # Filter valid dates and group by month
            valid_dates = self.merged_data[date_col].dropna()
            
            if valid_dates.empty:
                return None
            
            monthly_diagnoses = valid_dates.groupby(valid_dates.dt.to_period('M')).size()
            
            fig = px.line(
                x=monthly_diagnoses.index.astype(str),
                y=monthly_diagnoses.values,
                title="Diagnosis Trends Over Time",
                labels={'x': 'Month', 'y': 'Number of Diagnoses'}
            )
            
            fig.update_layout(
                height=400,
                xaxis_title="Month",
                yaxis_title="Number of Diagnoses"
            )
            
            return fig
        except:
            return None
    
    def create_diagnosis_cooccurrence(self) -> Optional[go.Figure]:
        """Create diagnosis co-occurrence heatmap"""
        try:
            # Get patients with multiple diagnoses
            patient_diagnosis_counts = self.merged_data['REGISTRY ID'].value_counts()
            patients_multiple_diagnoses = patient_diagnosis_counts[patient_diagnosis_counts > 1].index
            
            if len(patients_multiple_diagnoses) < 2:
                return None
            
            diagnosis_columns = [col for col in self.merged_data.columns if 'DIAGNOSIS' in col.upper()]
            if not diagnosis_columns:
                return None
            
            diagnosis_col = diagnosis_columns[0]
            
            # Get top diagnoses for co-occurrence analysis
            top_diagnoses = self.merged_data[diagnosis_col].value_counts().head(10).index
            
            # Create co-occurrence matrix
            cooccurrence_matrix = np.zeros((len(top_diagnoses), len(top_diagnoses)))
            
            for patient in patients_multiple_diagnoses:
                patient_diagnoses = self.merged_data[self.merged_data['REGISTRY ID'] == patient][diagnosis_col].tolist()
                patient_diagnoses = [d for d in patient_diagnoses if d in top_diagnoses]
                
                for i, diag1 in enumerate(top_diagnoses):
                    for j, diag2 in enumerate(top_diagnoses):
                        if diag1 in patient_diagnoses and diag2 in patient_diagnoses and i != j:
                            cooccurrence_matrix[i][j] += 1
            
            fig = px.imshow(
                cooccurrence_matrix,
                x=top_diagnoses,
                y=top_diagnoses,
                title="Diagnosis Co-occurrence Matrix",
                color_continuous_scale='Blues',
                aspect='auto'
            )
            
            fig.update_layout(
                height=600,
                xaxis_title="Co-occurring Diagnosis",
                yaxis_title="Primary Diagnosis"
            )
            
            return fig
        except:
            return None
    
    def create_patient_journey(self, patient_id: str) -> Optional[go.Figure]:
        """Create patient journey timeline"""
        patient_data = self.merged_data[self.merged_data['REGISTRY ID'] == patient_id]
        
        if patient_data.empty:
            return None
        
        date_columns = [col for col in patient_data.columns if 'DATE' in col.upper()]
        diagnosis_columns = [col for col in patient_data.columns if 'DIAGNOSIS' in col.upper()]
        
        if not date_columns or not diagnosis_columns:
            return None
        
        date_col = date_columns[0]
        diagnosis_col = diagnosis_columns[0]
        
        try:
            # Sort by date
            patient_data = patient_data.sort_values(date_col)
            
            fig = px.timeline(
                patient_data,
                x_start=date_col,
                x_end=date_col,
                y=diagnosis_col,
                title=f"Patient Journey - Registry ID: {patient_id}",
                color=diagnosis_col
            )
            
            fig.update_layout(
                height=400,
                xaxis_title="Date",
                yaxis_title="Diagnosis"
            )
            
            return fig
        except:
            # Fallback to scatter plot
            try:
                fig = px.scatter(
                    patient_data,
                    x=date_col,
                    y=diagnosis_col,
                    title=f"Patient Journey - Registry ID: {patient_id}",
                    hover_data=patient_data.columns.tolist()
                )
                
                fig.update_layout(height=400)
                return fig
            except:
                return None
    
    def create_age_diagnosis_analysis(self) -> Optional[go.Figure]:
        """Create age vs diagnosis analysis"""
        if 'AGE' not in self.merged_data.columns:
            return None
        
        diagnosis_columns = [col for col in self.merged_data.columns if 'DIAGNOSIS' in col.upper()]
        if not diagnosis_columns:
            return None
        
        diagnosis_col = diagnosis_columns[0]
        
        # Get top diagnoses
        top_diagnoses = self.merged_data[diagnosis_col].value_counts().head(10).index
        filtered_data = self.merged_data[self.merged_data[diagnosis_col].isin(top_diagnoses)]
        
        fig = px.box(
            filtered_data,
            x=diagnosis_col,
            y='AGE',
            title="Age Distribution by Diagnosis",
            color=diagnosis_col
        )
        
        fig.update_layout(
            height=500,
            xaxis_title="Diagnosis",
            yaxis_title="Age (years)",
            showlegend=False
        )
        
        fig.update_xaxes(tickangle=45)
        return fig
    
    def create_gender_diagnosis_analysis(self) -> Optional[go.Figure]:
        """Create gender vs diagnosis analysis"""
        if 'GENDER' not in self.merged_data.columns:
            return None
        
        diagnosis_columns = [col for col in self.merged_data.columns if 'DIAGNOSIS' in col.upper()]
        if not diagnosis_columns:
            return None
        
        diagnosis_col = diagnosis_columns[0]
        
        # Get top diagnoses
        top_diagnoses = self.merged_data[diagnosis_col].value_counts().head(8).index
        filtered_data = self.merged_data[self.merged_data[diagnosis_col].isin(top_diagnoses)]
        
        cross_tab = pd.crosstab(filtered_data[diagnosis_col], filtered_data['GENDER'])
        
        fig = px.bar(
            x=cross_tab.index,
            y=[cross_tab[col] for col in cross_tab.columns],
            title="Diagnosis Distribution by Gender",
            labels={'x': 'Diagnosis', 'y': 'Number of Cases'},
            barmode='group'
        )
        
        # Add legend for gender
        for i, gender in enumerate(cross_tab.columns):
            fig.data[i].name = gender
        
        fig.update_layout(
            height=500,
            xaxis_title="Diagnosis",
            yaxis_title="Number of Cases"
        )
        
        fig.update_xaxes(tickangle=45)
        return fig
    
    def create_department_analysis(self) -> Optional[go.Figure]:
        """Create department analysis"""
        dept_columns = [col for col in self.merged_data.columns if 'DEPT' in col.upper() or 'DEPARTMENT' in col.upper()]
        
        if not dept_columns:
            return None
        
        dept_col = dept_columns[0]
        dept_counts = self.merged_data[dept_col].value_counts()
        
        fig = px.pie(
            values=dept_counts.values,
            names=dept_counts.index,
            title="Cases by Department",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        
        fig.update_layout(height=500)
        return fig
