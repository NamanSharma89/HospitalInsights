# Hospital Data Analytics Dashboard

## Overview

This is a Streamlit-based hospital data analytics dashboard that processes Excel files containing patient and diagnosis information. The application provides interactive visualizations and data analysis capabilities for healthcare data management and insights.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit - chosen for rapid development of data-focused web applications
- **UI Components**: Streamlit widgets for file upload, filters, and data display
- **Layout**: Wide layout with expandable sidebar for controls and main area for visualizations
- **State Management**: Streamlit session state for maintaining data across user interactions

### Backend Architecture
- **Data Processing**: Object-oriented design with dedicated `DataProcessor` class
- **Visualization Engine**: `VisualizationManager` class handling all chart generation
- **Utilities**: Separate `utils.py` module for validation and formatting functions
- **Data Flow**: Excel upload → Processing → Validation → Visualization

## Key Components

### 1. Main Application (app.py)
- Entry point and UI orchestration
- Session state management for data persistence
- File upload handling and user interface layout
- Integration of all components

### 2. Data Processor (data_processor.py)
- **Purpose**: Handles Excel file ingestion and data cleaning
- **Key Features**:
  - Automatic sheet detection for patient and diagnosis data
  - Data validation and cleaning
  - Merging operations between patient and diagnosis datasets
- **Design Decision**: Separate class for data operations to maintain clean separation of concerns

### 3. Visualization Manager (visualizations.py)
- **Purpose**: Creates interactive charts and graphs using Plotly
- **Key Features**:
  - Age distribution histograms
  - Gender distribution pie charts
  - Modular chart creation methods
- **Technology Choice**: Plotly for interactive, professional-quality visualizations

### 4. Utilities (utils.py)
- **Purpose**: Common functions for data validation and formatting
- **Key Features**:
  - Data quality validation
  - Error and warning reporting
  - Reusable utility functions

## Data Flow

1. **File Upload**: User uploads Excel file through Streamlit interface
2. **Sheet Detection**: System automatically identifies patient and diagnosis sheets
3. **Data Processing**: 
   - Clean and validate data
   - Check for required columns (REGISTRY ID)
   - Handle missing values and duplicates
4. **Data Merging**: Combine patient and diagnosis data on REGISTRY ID
5. **Visualization**: Generate interactive charts and summary statistics
6. **State Management**: Store processed data in session state for persistence

## External Dependencies

### Core Libraries
- **streamlit**: Web application framework
- **pandas**: Data manipulation and analysis
- **plotly**: Interactive visualization library
- **numpy**: Numerical computing support

### Design Rationale
- **Streamlit**: Chosen for rapid prototyping and ease of deployment for data applications
- **Plotly**: Selected over matplotlib for interactive capabilities and professional appearance
- **Pandas**: Industry standard for data manipulation in Python

## Deployment Strategy

### Current Setup
- Designed for local development and testing
- Streamlit's built-in development server
- Session-based state management for single-user scenarios

### Production Considerations
- Can be deployed to Streamlit Cloud, Heroku, or similar platforms
- File upload handling suitable for moderate-sized Excel files
- Memory-based data storage (no persistent database currently)

### Scalability Notes
- Current architecture supports single-user sessions
- For multi-user production deployment, consider adding:
  - Database integration for data persistence
  - User authentication and session management
  - File storage optimization for large datasets

## Key Architectural Decisions

### Problem: Excel File Processing
- **Solution**: Automatic sheet detection with fallback naming conventions
- **Rationale**: Reduces user friction by intelligently finding relevant data sheets
- **Alternative**: Manual sheet selection - rejected for poor user experience

### Problem: Data Validation
- **Solution**: Multi-layered validation with errors, warnings, and info messages
- **Rationale**: Provides clear feedback while handling real-world data quality issues
- **Benefits**: Robust error handling and user guidance

### Problem: Visualization Architecture
- **Solution**: Separate VisualizationManager class with modular chart methods
- **Rationale**: Maintains clean separation between data processing and presentation
- **Benefits**: Easy to extend with new chart types and maintain existing visualizations

### Problem: State Management
- **Solution**: Streamlit session state for data persistence
- **Rationale**: Prevents re-processing data on each interaction
- **Trade-off**: Memory usage vs. performance optimization