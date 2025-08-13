# Excel Validator Pipeline

A robust and comprehensive pipeline for validating, cleaning, and extracting data from Excel files with **IRL (Information Requirements List) validation** using LLM analysis. This tool handles various Excel formats, structures, and provides intelligent requirement matching without exposing sensitive data.

## Features

### Core Capabilities
- **Multi-format Support**: Handles .xlsx, .xls, .xlsm, .xlsb, and .csv files
- **Automatic Structure Detection**: Identifies whether data is structured (tables), unstructured (key-value pairs), or semi-structured
- **Intelligent Table Detection**: Finds tables even when they start from arbitrary rows/columns
- **Hierarchical Key-Value Extraction**: Builds proper hierarchy for unstructured data with headings and sub-headings
- **Advanced Date-Time Recognition**: Supports various formats (1-01-2025, 1 Aug 2025, etc.) with separators like -, _, /, spaces, or mixed
- **Entity Detection**: Identifies company names, investor names, and other business entities
- **IRL Requirement Validation**: Uses LLM to compare file metadata against Information Requirements Lists

### Enhanced Data Analysis
- **Robust Date Parsing**: Handles multiple date formats, quarters (Q1-2024), fiscal years, relative periods
- **Company Name Detection**: Identifies primary entities and business relationships
- **Period Analysis**: Extracts min/max dates, fiscal years, quarters covered
- **Privacy-Safe Metadata**: Extracts structure and statistics without exposing sensitive values
- **LLM-Powered Validation**: Intelligent matching of files to requirements using Claude/OpenAI

### Performance Features
- **Parallel Processing**: Multi-threading and multi-processing support for handling multiple files
- **Configurable Timeouts**: Prevents hanging on problematic files
- **Memory Management**: Chunked processing for large files
- **Multiple Fallback Methods**: Tries different libraries if one fails

### Output Options
- **HTML Reports**: Beautiful, interactive reports with data previews
- **IRL Validation Reports**: Comprehensive requirement compliance reports
- **JSON Export**: Complete structured data export with metadata
- **CSV Summary**: Quick overview in spreadsheet format

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Standard Excel Processing

```python
from Validator import ExcelValidationPipeline, PipelineConfig

# Create pipeline with default configuration
pipeline = ExcelValidationPipeline()

# Process a single file
result = pipeline.process_file("path/to/file.xlsx")

# Process multiple files in a directory
results = pipeline.validate_directory("path/to/directory")
```

### IRL Requirements Validation

```python
from Validator import validate_against_irl_requirements

# Define IRL requirements as provided by user
irl_requirements = {
    "Revenue Analysis": "a) Monthly revenue breakdown for 2024, b) Quarterly variance analysis", 
    "Balance Sheet": "a) Current assets as of Dec 31 2024, b) Long-term debt schedule",
    "Cash Flow": "a) Operating cash flow detail Q4 2024, b) Free cash flow calculation"
}

# List of Excel files to validate
file_paths = [
    "revenue_data.xlsx",
    "balance_sheet.xlsx", 
    "cashflow_report.xlsx"
]

# Run IRL validation
result = validate_against_irl_requirements(
    file_paths=file_paths,
    irl_requirements=irl_requirements
)

# Check results
print(f"Status: {result['overall_compliance']['status']}")
print(f"Confidence: {result['overall_compliance']['confidence_score']:.2f}")

# View detailed analysis
for category, analysis in result['detailed_findings']['by_requirement'].items():
    print(f"{category}: {analysis['status']}")
    if analysis['gaps']:
        print(f"  Issues: {', '.join(analysis['gaps'])}")
```

### With Custom Configuration

```python
from Validator import ExcelValidationPipeline, PipelineConfig

# Create custom configuration
config = PipelineConfig(
    output_dir="my_output",
    max_workers=8,
    use_multiprocessing=True,
    remove_duplicates=True,
    infer_data_types=True,
    max_scan_rows=50,
    max_scan_cols=50
)

# Create pipeline with custom config
pipeline = ExcelValidationPipeline(config)

# Process files
results = pipeline.validate_directory("path/to/excel/files")
```

### Using Pre-configured Profiles

```python
from Validator.config import ProfiledConfig

# Fast scanning for quick overview
config = ProfiledConfig.fast_scan()

# Thorough analysis for detailed validation
config = ProfiledConfig.thorough_analysis()

# Optimized for large files
config = ProfiledConfig.large_files()

# Optimized for unstructured data
config = ProfiledConfig.unstructured_focus()

pipeline = ExcelValidationPipeline(config)
```

### Command Line Interface

#### Standard Processing
```bash
# Process a single file
python -m Validator.main input_file.xlsx -o output_dir

# Process a directory
python -m Validator.main input_directory/ -o output_dir --parallel

# Use a profile
python -m Validator.main input_directory/ --profile thorough

# With custom options
python -m Validator.main input_file.xlsx \
    --max-scan-rows 50 \
    --max-scan-cols 50 \
    --remove-duplicates \
    --workers 8 \
    -v  # verbose output
```

#### IRL Validation via CLI
```bash
# Using IRL requirements from JSON file
python -m Validator.main input_directory/ \
    --irl-file requirements.json \
    --parallel \
    -o irl_results

# Using IRL requirements as JSON string
python -m Validator.main input_directory/ \
    --irl-json '{"Revenue Analysis": "a) Monthly reports, b) Quarterly data"}' \
    --profile thorough

# Example requirements.json file:
{
    "Revenue Analysis": "a) Monthly revenue by product line 2024, b) Quarterly variance report",
    "Financial Position": "a) Balance sheet Dec 31 2024, b) Assets breakdown", 
    "Cash Management": "a) Cash flow Q4 2024, b) Working capital analysis"
}
```

## Configuration Options

### Processing Settings
- `max_workers`: Number of parallel workers (default: CPU count)
- `use_multiprocessing`: Use multiprocessing instead of threading
- `file_timeout`: Maximum time per file in seconds (default: 300)

### Structure Detection
- `max_scan_rows`: Rows to scan for structure detection (default: 20)
- `max_scan_cols`: Columns to scan for structure detection (default: 20)
- `min_data_density`: Minimum data density to consider structured (default: 0.3)
- `header_confidence_threshold`: Confidence threshold for header detection (default: 0.7)

### Data Cleaning
- `replace_missing_with`: Value to replace missing data (default: None)
- `trim_whitespace`: Remove leading/trailing whitespace (default: True)
- `standardize_dates`: Convert dates to standard format (default: True)
- `remove_duplicates`: Remove duplicate rows (default: False)
- `infer_data_types`: Automatically detect column data types (default: True)

## Output Structure

### Standard Processing Output
```json
{
  "file_path": "path/to/file.xlsx",
  "status": "success",
  "sheets": {
    "Sheet1": {
      "structure_type": "structured",
      "cleaned_data": {
        "columns": ["ID", "Name", "Date", "Amount"],
        "data": [...],
        "data_types": {
          "ID": "integer", 
          "Name": "text",
          "Date": "date",
          "Amount": "float"
        },
        "entity_columns": {
          "Company": {
            "unique_entities": 5,
            "primary_entity": "ABC Corp",
            "entity_types": {"companies": ["ABC Corp", "XYZ Inc"]}
          }
        },
        "date_columns": {
          "Date": {
            "min_date": "2024-01-01",
            "max_date": "2024-12-31",
            "granularity": "daily"
          }
        },
        "period_info": {
          "Date": {
            "start_year": 2024,
            "end_year": 2024,
            "fiscal_years": [2024]
          }
        }
      }
    }
  }
}
```

### IRL Validation Output
```json
{
  "overall_compliance": {
    "status": "COMPLIANT|PARTIALLY_COMPLIANT|NON_COMPLIANT",
    "confidence_score": 0.85,
    "summary": "Files meet most requirements with minor gaps"
  },
  "file_analysis": {
    "total_files_submitted": 3,
    "expected_files": 3,
    "missing_files": [],
    "file_matches": {
      "Revenue Analysis": {
        "expected": "Monthly revenue breakdown",
        "found": "revenue_data.xlsx",
        "match_quality": "GOOD"
      }
    }
  },
  "entity_analysis": {
    "required_entities": ["ABC Corp"],
    "found_entities": ["ABC Corp", "ABC Corporation"],
    "entity_matches": {
      "ABC Corp": {
        "found": true,
        "confidence": 0.9
      }
    }
  },
  "period_analysis": {
    "required_periods": ["2024"],
    "period_coverage": {
      "fully_covered": ["2024"],
      "missing": []
    }
  },
  "recommendations": [
    "Revenue file covers all required periods",
    "Consider standardizing entity names"
  ]
}
```

## Edge Cases Handled

1. **Tables starting from arbitrary positions**: Automatically detects table boundaries
2. **Mixed content**: Handles sheets with both structured and unstructured data
3. **Merged cells**: Properly processes merged cell ranges
4. **Multiple encodings**: Detects and handles different file encodings
5. **Corrupted files**: Falls back to alternative reading methods
6. **Large files**: Chunks data to prevent memory issues
7. **Formula cells**: Can read calculated values
8. **Date formats**: Recognizes and standardizes various date formats
9. **Missing headers**: Generates column names when headers are missing
10. **Sparse data**: Handles sheets with scattered data points

## Error Handling

The pipeline includes comprehensive error handling:
- Individual file errors don't stop batch processing
- Detailed error logging with tracebacks
- Fallback methods for file reading
- Timeout protection for hanging operations
- Graceful degradation for partially readable files

## Performance Tips

1. **For large batches**: Use `use_multiprocessing=True`
2. **For quick scanning**: Use the `fast_scan()` profile
3. **For memory-constrained systems**: Reduce `chunk_size` and `max_workers`
4. **For network drives**: Increase `file_timeout`

## Complete IRL Validation Example

```python
from Validator import validate_against_irl_requirements, PipelineConfig

# Real-world IRL requirements as received from client
irl_requirements = {
    "Revenue Analysis": "a) Monthly revenue breakdown by product line for FY 2024, b) Quarterly variance analysis against budget, c) Revenue recognition schedule with deferred amounts",
    
    "Balance Sheet Analysis": "a) Current assets detail as of December 31, 2024, b) Long-term debt maturity schedule, c) Stockholders equity rollforward",
    
    "Cash Flow Statement": "a) Operating cash flow detail for Q4 2024, b) Capital expenditure breakdown, c) Free cash flow calculation and reconciliation",
    
    "Financial Ratios": "a) Liquidity ratios quarterly trend, b) Leverage ratios with covenant compliance, c) Profitability metrics vs industry benchmarks"
}

# Configure for comprehensive analysis
config = {
    'output_dir': 'irl_validation_results',
    'max_scan_rows': 50,        # Deep scanning for complex structures
    'max_scan_cols': 30,        # Wide tables common in financial data
    'infer_data_types': True,   # Critical for validation accuracy
    'standardize_dates': True,  # Handle various date formats
    'use_multiprocessing': True # Faster processing
}

# List of submitted Excel files
files_to_validate = [
    "CompanyABC_Revenue_Analysis_2024.xlsx",
    "CompanyABC_Balance_Sheet_Dec2024.xlsx", 
    "CompanyABC_CashFlow_Q4_2024.xlsx",
    "CompanyABC_Financial_Ratios_Quarterly.xlsx"
]

# Run comprehensive IRL validation
result = validate_against_irl_requirements(
    file_paths=files_to_validate,
    irl_requirements=irl_requirements,
    config=config
)

# Analyze results
compliance = result['overall_compliance']
print(f"Overall Status: {compliance['status']}")
print(f"Confidence Score: {compliance['confidence_score']:.2f}")

# Check specific requirement compliance
for requirement, details in result['detailed_findings']['by_requirement'].items():
    print(f"\n{requirement}: {details['status']}")
    if details.get('gaps'):
        print(f"  Issues: {', '.join(details['gaps'])}")
        
# View entity and period analysis
entities = result['entity_analysis']
if entities['found_entities']:
    print(f"\nCompanies Found: {', '.join(entities['found_entities'][:3])}...")
    
periods = result['period_analysis']['period_coverage']
if periods['fully_covered']:
    print(f"Time Periods Covered: {', '.join(periods['fully_covered'])}")
if periods['missing']:
    print(f"Missing Periods: {', '.join(periods['missing'])}")

print(f"\nDetailed reports saved to: {config['output_dir']}")
```

## Advanced Date-Time Recognition

The validator handles complex date formats commonly found in financial documents:

```python
# Supported date formats:
dates = [
    "1-01-2025", "01/01/2025", "2025-01-01", "Jan 1, 2025",
    "1 January 2025", "Q1-2025", "FY2025", "Dec 2024", 
    "2024/Q4", "20250101", "as of 12/31/2024"
]

# All are automatically detected and standardized to ISO format
# Extracts: min_date, max_date, fiscal_years, quarters covered
```

## License

MIT License