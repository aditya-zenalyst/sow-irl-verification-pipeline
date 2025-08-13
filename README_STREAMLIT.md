# Zenalyst Streamlit Application

## Overview
This Streamlit application provides a visual interface for the complete Zenalyst due diligence workflow, from SOW generation to validation.

## Features

### Complete Workflow Implementation:

1. **SOW Generation/Upload (Step 1)**
   - **Option 1: Generate New SOW from Documents**
     - Upload multiple documents (PDF, Excel, Word, TXT)
     - System analyzes documents using AI
     - Automatically generates comprehensive SOW
     - Extracts company information and requirements
   - **Option 2: Upload Existing SOW**
     - Direct upload of pre-existing SOW files
     - Supports TXT, PDF, DOCX formats

2. **Interactive Option Selection (Step 2)**
   - Parses SOW into analysis sections
   - Each section shows as expandable card with procedures
   - Checkbox selection for each procedure
   - Bulk operations (Select All/Clear All)
   - Validates minimum selection requirements
   - Reconstructs customized SOW based on selections

3. **IRL Excel Generation (Step 3)**
   - Converts customized SOW to IRL Excel format
   - Automatic generation of information requirements
   - Download generated Excel file
   - Preview IRL content and statistics

4. **File Upload & Validation (Step 4)**
   - Multiple file upload for validation
   - Supports Excel, CSV formats
   - Validates against IRL requirements
   - Real-time validation progress

5. **Results & Visualization (Step 5)**
   - Interactive charts and metrics
   - Detailed validation results per file
   - Export reports (JSON, CSV)
   - Success/failure visualizations

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup Instructions

1. **Install Dependencies**
```bash
pip install -r requirements_streamlit.txt
```

2. **Run the Application**
```bash
streamlit run streamlit_app.py
```

3. **Access the Application**
   - Open browser at `http://localhost:8501`
   - The application will launch automatically

## Usage Guide

### Workflow Steps:

#### Step 1: Generate or Upload SOW
1. Choose between generating new SOW or uploading existing
2. For new SOW generation:
   - Enter Investor ID and Investee ID
   - Upload company documents (financial statements, contracts, etc.)
   - Add optional context
   - Click "Generate SOW"
3. For existing SOW:
   - Upload your SOW file directly

#### Step 2: Customize Scope
1. Review parsed analysis sections
2. Select/deselect procedures using checkboxes
3. Use bulk selection tools for efficiency
4. Click "Generate Customized SOW"

#### Step 3: Generate IRL
1. Review customized SOW
2. Enter investor/investee details
3. Click "Generate IRL Excel"
4. Download the generated Excel file

#### Step 4: Upload & Validate
1. Upload Excel files per IRL requirements
2. Click "Validate Files"
3. Review validation progress

#### Step 5: View Results
1. Review validation metrics
2. Check detailed results per file
3. Export reports as needed

## Key Features

### Visual Enhancements
- Professional UI with custom styling
- Color-coded status indicators
- Progress tracking sidebar
- Interactive Plotly charts
- Responsive layout

### Edge Case Handling
- Minimum selection validation
- Empty section handling
- Clear error messages
- File format validation

### State Management
- Persistent workflow state
- Reset functionality
- Session state preservation

## File Structure
```
combined/
├── streamlit_app.py          # Main Streamlit application
├── requirements_streamlit.txt # Dependencies
├── SOW/                      # SOW generation module
├── IRL/                      # IRL processing module
├── Validator/                # Validation module
└── README_STREAMLIT.md       # This file
```

## Troubleshooting

### Common Issues:

1. **Import Errors**
   - Ensure all dependencies are installed
   - Check Python path includes project directories

2. **File Upload Issues**
   - Verify file formats are supported
   - Check file size limits (100MB max)

3. **Pipeline Initialization**
   - Ensure all required modules are present
   - Check API keys for Claude integration

## Support
For issues or questions, please check the logs in the terminal where Streamlit is running.

## Version
v1.0 - Initial release with complete workflow implementation