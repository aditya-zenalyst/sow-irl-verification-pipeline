# DD SOW LLM - Professional Due Diligence System
*Dynamic Due Diligence Scope of Work Generation using Claude Sonnet*

An AI-powered financial analysis system that generates comprehensive, institutional-quality due diligence scopes from any financial PDF. The system automatically adapts to different company types and financial situations.

## 🚀 Quick Start

### 1. Navigate to SOW LLM Directory
```bash
cd "SOW LLM"
```

### 2. Install Dependencies
```bash
pip install -r ../requirements.txt
```

### 3. Set Up API Key
Your Claude API key is already configured in `.env` file.

### 4. Run Analysis
```bash
python dynamic_dd_pipeline.py "your_financial_pdf.pdf"
```

## 📁 System Structure

```
NEW LLM ZEN/
├── SOW LLM/                          # Current production system
│   ├── dynamic_dd_pipeline.py        # Main pipeline (cost-optimized)
│   ├── optimized_dd_prompt.txt       # Smart prompt (4K tokens)
│   ├── claude_integration.py         # API integration
│   ├── ocr_handler.py                # PDF processing (OCR + digital)
│   ├── config.py                     # Configuration
│   ├── .env                          # API keys
│   ├── version_tracker.json          # Output versioning
│   └── extracted_text.txt            # Temp extraction file
├── IRL LLM/                          # Future system (planned)
├── requirements.txt                  # Python dependencies
└── Reference Files/                  # Templates and samples
    ├── Master Fdd Expanded.docx      # Comprehensive DD template
    ├── WhatsApp Images/              # Professional format references
    └── ABC-Financials-V1.pdf         # Test file
```

## 🎯 Key Features

### ✅ **Cost-Optimized Generation**
- **4K tokens** instead of 8K (50% cost savings)
- Single API call generates complete scope
- Smart prompt compression maintains quality

### ✅ **Universal PDF Support**
- **Digital PDFs**: Direct text extraction
- **Scanned PDFs**: OCR with 300 DPI processing
- **Automatic detection** and processing

### ✅ **Professional Output Quality**
- **Executive Summary & Risk Analysis**: Company-specific insights
- **14 Standard DD Sections**: All institutional procedures
- **No unwanted sections**: Clean format (no timelines/deliverables)
- **Version tracking**: Automatic v1, v2, v3... numbering

### ✅ **Dynamic Analysis**
- **Company name extraction**: Automatic from document
- **Industry adaptation**: System adapts to business type
- **Risk prioritization**: Highlights key concern areas
- **Financial insights**: Data-driven observations

## 📊 Sample Output Structure

```
FINANCIAL DUE DILIGENCE SCOPE OF WORK
==================================================
Company: CROSSWAYS VERTICAL SOLUTIONS PRIVATE LIMITED
Generated: August 01, 2025

📊 SCOPE SUMMARY
--------------------
Analysis Areas: 14
Estimated Hours: 350
Complexity Level: High

**EXECUTIVE SUMMARY & RISK ANALYSIS**
====================================
[Company-specific financial position analysis, key risks, and priority areas]

**DD SCOPE TABLE**
=================
Financial periods: [Actual periods from data]

| Analysis Area | Detailed Procedures |
|--------------|-------------------|
| Quality of Earnings Analysis | [8-10 specific procedures] |
| Income Statement Analysis | [8-10 specific procedures] |
| Working Capital Management | [8-10 specific procedures] |
[... all 14 sections]
```

## 🔧 Technical Architecture

### **Pipeline Flow:**
1. **PDF Processing** → OCR/Digital text extraction
2. **Company Extraction** → LLM identifies company name
3. **Risk Analysis** → Dynamic requirement generation
4. **DD Scope Generation** → Optimized 4K token prompt
5. **Output Formatting** → Clean professional format
6. **Version Tracking** → Automatic file versioning

### **Cost Optimization:**
- **Before**: 8,000 tokens = High cost + truncation issues
- **After**: 4,000 tokens = 50% cost savings + complete output

## 💡 Usage Examples

### Basic Analysis
```bash
python dynamic_dd_pipeline.py "Balance Sheet Company 2022.pdf"
```

### Supported File Types
- Digital PDFs (financial statements, audit reports)
- Scanned PDFs (automatically detected and processed)
- Multi-page financial documents

## 📈 Tested Companies

### **Crossways Vertical Solutions**
- 107% revenue growth analysis
- Working capital stress identification
- Debt structure risk assessment
- **Output**: 9 versions with progressive improvements

### **Pavitra Conbuild Private Limited**
- Construction industry adaptation
- Real estate transaction analysis
- Regulatory compliance focus
- **Output**: Professional institutional format

## 🛠 System Components

### **SOW LLM** (Current Production System)
**Purpose**: Generate due diligence scopes from financial PDFs
**Status**: ✅ Production ready, cost-optimized
**Output**: Professional DD scope documents

### **IRL LLM** (Planned Future System)
**Purpose**: Will consume SOW LLM output for next-stage processing
**Status**: 📋 Folder created, ready for development
**Integration**: Will call SOW LLM as dependency

## 🔒 Security Features

- API keys stored in `.env` file
- No hardcoded sensitive information
- Professional legal compliance
- Data extraction to temporary files only

## 📋 Quality Metrics

- **Format Compliance**: Matches institutional consulting standards
- **Content Quality**: 14 comprehensive DD sections
- **Cost Efficiency**: 50% token reduction achieved
- **Processing Speed**: Single API call completion
- **Accuracy**: Company-specific insights and procedures

## 🎯 Next Development Phase

The **IRL LLM** system will:
1. Take SOW LLM output as input
2. Process DD scopes for further analysis
3. Call SOW LLM via API/direct integration
4. Extend the due diligence workflow

---

*Built with Claude Sonnet for institutional-quality financial due diligence scope generation*