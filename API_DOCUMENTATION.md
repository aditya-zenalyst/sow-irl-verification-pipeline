# Zenalyst API Documentation

## Overview

The Zenalyst API system provides a unified interface for managing the complete due diligence workflow:
1. **SOW Generation** - Generate Statement of Work from investor/investee data and documents
2. **Excel Conversion** - Convert SOW text to structured Excel format (IRL)
3. **IRL Validation** - Validate Excel files against IRL requirements

## Getting Started

### Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
# Create .env file with your API keys
CLAUDE_API_KEY=your_api_key_here
```

3. Run the API server:
```bash
python api_main.py
```

The server will start on `http://localhost:5000`

## API Endpoints

### 1. Health Check

**Endpoint:** `GET /health`

Check the health status of the API and all pipelines.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-10T10:00:00",
  "pipelines": {
    "sow": true,
    "irl": true,
    "validator": true
  }
}
```

---

### 2. Generate SOW

**Endpoint:** `POST /sow/generate`

Generate Statement of Work (SOW) text from investor/investee data and supporting documents.

**Request Body:**
```json
{
  "investor_id": "INV001",
  "investee_id": "ABC_Company",
  "documents": [
    {
      "name": "financials.pdf",
      "type": "pdf",
      "path": "/path/to/financials.pdf"
    },
    {
      "name": "balance_sheet.txt",
      "type": "txt",
      "path": "/path/to/balance_sheet.txt"
    }
  ],
  "additional_context": "Focus on revenue quality and working capital analysis"
}
```

**Parameters:**
- `investor_id` (required): Unique identifier for the investor
- `investee_id` (required): Name or identifier of the company being evaluated
- `documents` (optional): Array of documents to process
  - `name`: Display name of the document
  - `type`: File type (`pdf`, `txt`, `excel`)
  - `path`: File system path to the document
- `additional_context` (optional): Additional instructions or context for SOW generation

**Response:**
```json
{
  "status": "success",
  "investor_id": "INV001",
  "investee_id": "ABC_Company",
  "sow_text": "Due Diligence Scope of Work for ABC Company...",
  "output_file": "ABC_Company_DD_SOW_v1.txt",
  "timestamp": "2025-08-10T10:00:00"
}
```

**Example cURL:**
```bash
curl -X POST http://localhost:5000/sow/generate \
  -H "Content-Type: application/json" \
  -d '{
    "investor_id": "INV001",
    "investee_id": "ABC_Company",
    "documents": [
      {
        "name": "financials.pdf",
        "type": "pdf",
        "path": "./documents/financials.pdf"
      }
    ]
  }'
```

---

### 3. Convert SOW to Excel

**Endpoint:** `POST /sow/to_excel`

Convert SOW text to structured Excel format (Information Requirements List).

**Request Body:**
```json
{
  "investor_id": "INV001",
  "investee_id": "ABC_Company",
  "sow_text": "Due Diligence Scope of Work...",
  "sow_file_path": "/path/to/sow_file.txt"
}
```

**Parameters:**
- `investor_id` (required): Unique identifier for the investor
- `investee_id` (required): Name or identifier of the company
- `sow_text` (optional): SOW content as text
- `sow_file_path` (optional): Path to SOW file (used if `sow_text` not provided)

**Note:** Either `sow_text` or `sow_file_path` must be provided.

**Response:**
Returns the Excel file as a downloadable attachment.

**Example cURL:**
```bash
curl -X POST http://localhost:5000/sow/to_excel \
  -H "Content-Type: application/json" \
  -d '{
    "investor_id": "INV001",
    "investee_id": "ABC_Company",
    "sow_file_path": "./ABC_Company_DD_SOW_v1.txt"
  }' \
  -o ABC_Company_IRL.xlsx
```

---

### 4. Validate IRL

**Endpoint:** `POST /irl/validate`

Validate Excel files against IRL requirements.

**Request (Form-Data):**
```
investor_id: INV001
investee_id: ABC_Company
irl_file: [file upload]
excel_files: [multiple file uploads]
validation_rules: {"custom": "rules"}
```

**Request (JSON):**
```json
{
  "investor_id": "INV001",
  "investee_id": "ABC_Company",
  "irl_file": "/path/to/irl.xlsx",
  "excel_files": [
    "/path/to/data1.xlsx",
    "/path/to/data2.xlsx"
  ],
  "validation_rules": {
    "check_completeness": true,
    "validate_formats": true
  }
}
```

**Parameters:**
- `investor_id` (required): Unique identifier for the investor
- `investee_id` (required): Name or identifier of the company
- `irl_file` (optional): IRL Excel file for validation requirements
- `excel_files` (optional): List of Excel files to validate
- `validation_rules` (optional): Custom validation rules

**Response:**
```json
{
  "status": "success",
  "investor_id": "INV001",
  "investee_id": "ABC_Company",
  "validation_results": [
    {
      "file": "financial_data.xlsx",
      "validation": {
        "status": "success",
        "issues": [],
        "warnings": []
      }
    }
  ],
  "summary": {
    "total_files": 2,
    "successful": 2,
    "failed": 0,
    "validation_timestamp": "2025-08-10T10:00:00"
  },
  "report_file": "validation_output/INV001_ABC_Company_20250810_100000/validation_report.json",
  "timestamp": "2025-08-10T10:00:00"
}
```

**Example cURL (Form-Data):**
```bash
curl -X POST http://localhost:5000/irl/validate \
  -F "investor_id=INV001" \
  -F "investee_id=ABC_Company" \
  -F "irl_file=@./irl.xlsx" \
  -F "excel_files=@./data1.xlsx" \
  -F "excel_files=@./data2.xlsx"
```

---

### 5. Complete Workflow

**Endpoint:** `POST /workflow/complete`

Execute the complete workflow: SOW Generation → Excel Conversion → Validation.

**Request Body:**
```json
{
  "investor_id": "INV001",
  "investee_id": "ABC_Company",
  "documents": [
    {
      "name": "financials.pdf",
      "type": "pdf",
      "path": "/path/to/financials.pdf"
    }
  ],
  "validation_files": [
    "/path/to/data1.xlsx",
    "/path/to/data2.xlsx"
  ]
}
```

**Parameters:**
- All parameters from `/sow/generate`
- `validation_files` (optional): Excel files to validate after IRL generation

**Response:**
```json
{
  "status": "success",
  "workflow": "complete",
  "sow_generation": {
    "status": "success",
    "sow_text": "...",
    "output_file": "ABC_Company_DD_SOW_v1.txt"
  },
  "excel_conversion": "completed",
  "validation": {
    "status": "success",
    "validation_results": [...],
    "summary": {...}
  },
  "timestamp": "2025-08-10T10:00:00"
}
```

## Workflow Guide

### Standard Workflow

1. **Generate SOW**: Call `/sow/generate` with investor/investee IDs and relevant documents
2. **Convert to Excel**: Use the SOW text or file path with `/sow/to_excel` to create IRL
3. **Validate Data**: Upload IRL and data files to `/irl/validate` for compliance checking

### Quick Start Example

```python
import requests
import json

# Base URL
base_url = "http://localhost:5000"

# Step 1: Generate SOW
sow_response = requests.post(
    f"{base_url}/sow/generate",
    json={
        "investor_id": "INV001",
        "investee_id": "ABC_Company",
        "documents": [
            {
                "name": "financials.pdf",
                "type": "pdf",
                "path": "./financials.pdf"
            }
        ]
    }
)
sow_data = sow_response.json()
print(f"SOW Generated: {sow_data['output_file']}")

# Step 2: Convert to Excel
excel_response = requests.post(
    f"{base_url}/sow/to_excel",
    json={
        "investor_id": "INV001",
        "investee_id": "ABC_Company",
        "sow_text": sow_data["sow_text"]
    }
)
# Save Excel file
with open("IRL.xlsx", "wb") as f:
    f.write(excel_response.content)
print("IRL Excel created: IRL.xlsx")

# Step 3: Validate (if you have data files)
with open("IRL.xlsx", "rb") as irl_file:
    with open("data.xlsx", "rb") as data_file:
        validation_response = requests.post(
            f"{base_url}/irl/validate",
            files={
                "irl_file": irl_file,
                "excel_files": data_file
            },
            data={
                "investor_id": "INV001",
                "investee_id": "ABC_Company"
            }
        )
validation_data = validation_response.json()
print(f"Validation Status: {validation_data['status']}")
```

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": "Error message describing what went wrong"
}
```

**HTTP Status Codes:**
- `200`: Success
- `400`: Bad Request (missing required parameters)
- `404`: Endpoint not found
- `500`: Internal Server Error

## File Formats

### SOW Text Format
The SOW is generated as a structured text document containing:
- Company information
- Financial periods
- Due diligence scope areas
- Detailed procedures for each area

### IRL Excel Format
The IRL Excel file contains:
- Header with company and period information
- Columns: S.No., Section, Information Requirement, Priority, Comments
- Detailed data requirements organized by DD sections

### Validation Report Format
The validation report includes:
- File-by-file validation results
- Identified issues and warnings
- Compliance status against IRL requirements
- Summary statistics

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# API Keys
CLAUDE_API_KEY=your_claude_api_key

# Server Configuration
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=True

# File Limits
MAX_FILE_SIZE=104857600  # 100MB in bytes

# Processing
PARALLEL_PROCESSING=True
MAX_WORKERS=4
```

### Pipeline Configuration

Each pipeline can be configured through their respective config files:
- `SOW-main/config.py` - SOW generation settings
- `IRL-main/config.py` - IRL generation settings  
- `Validator/config.py` - Validation settings

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python version compatibility (Python 3.8+ required)

2. **API Key Issues**
   - Verify CLAUDE_API_KEY is set in `.env` file
   - Check API key validity and quota

3. **File Processing Errors**
   - Ensure file paths are absolute paths
   - Check file permissions
   - Verify file formats are supported

4. **Memory Issues**
   - For large files, increase available memory
   - Use pagination for bulk processing
   - Consider splitting large Excel files

### Debug Mode

Enable debug logging by setting:
```python
app.run(debug=True)
```

Or via environment variable:
```bash
export FLASK_DEBUG=1
```

## Support

For issues or questions:
1. Check the error logs in `validation_output/logs/`
2. Review the API response error messages
3. Ensure all file paths are correct and accessible

## Version History

- **v1.0.0** - Initial release with three core endpoints
- Supports SOW generation from multiple document types
- Excel IRL generation with version tracking
- Comprehensive validation against IRL requirements