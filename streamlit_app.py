#!/usr/bin/env python3
"""
Zenalyst Streamlit Application
==============================
Interactive web interface for SOW generation, IRL processing, and validation workflows.
"""

import streamlit as st
import pandas as pd
import json
import os
import sys
import re
from pathlib import Path
from datetime import datetime
import tempfile
import shutil
from typing import Dict, Any, List, Optional, Tuple
import plotly.express as px
import plotly.graph_objects as go

# Add project directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'SOW'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'IRL'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Validator'))

# Import modules
try:
    from SOW.dynamic_dd_pipeline import DynamicDueDiligencePipeline
    from IRL.irl_dd_pipeline import IRLDueDiligencePipeline
    from Validator.pipeline import ExcelValidationPipeline
    from Validator.config import PipelineConfig
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Zenalyst - Financial Due Diligence Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1e3a8a;
        text-align: center;
        padding: 1rem 0;
        border-bottom: 3px solid #3b82f6;
        margin-bottom: 2rem;
    }
    .step-header {
        font-size: 1.5rem;
        color: #1e40af;
        margin: 1.5rem 0 1rem 0;
        padding: 0.5rem;
        background: linear-gradient(90deg, #eff6ff 0%, #ffffff 100%);
        border-left: 4px solid #3b82f6;
    }
    .info-box {
        background-color: #f0f9ff;
        border: 1px solid #3b82f6;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #f0fdf4;
        border: 1px solid #22c55e;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fef3c7;
        border: 1px solid #f59e0b;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #fef2f2;
        border: 1px solid #ef4444;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .stButton > button {
        background-color: #3b82f6;
        color: white;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        border: none;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        background-color: #2563eb;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .analysis-section {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .section-title {
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'workflow_state' not in st.session_state:
    st.session_state.workflow_state = 'start'
if 'sow_content' not in st.session_state:
    st.session_state.sow_content = None
if 'sow_sections' not in st.session_state:
    st.session_state.sow_sections = {}
if 'selected_procedures' not in st.session_state:
    st.session_state.selected_procedures = {}
if 'customized_sow' not in st.session_state:
    st.session_state.customized_sow = None
if 'customized_sow_path' not in st.session_state:
    st.session_state.customized_sow_path = None
if 'original_sow_filename' not in st.session_state:
    st.session_state.original_sow_filename = None
if 'irl_excel_path' not in st.session_state:
    st.session_state.irl_excel_path = None
if 'validation_results' not in st.session_state:
    st.session_state.validation_results = None
if 'pipelines' not in st.session_state:
    st.session_state.pipelines = {
        'sow': None,
        'irl': None,
        'validator': None
    }

@st.cache_resource
def initialize_pipelines():
    """Initialize all processing pipelines"""
    try:
        sow_pipeline = DynamicDueDiligencePipeline()
        irl_pipeline = IRLDueDiligencePipeline()
        config = PipelineConfig()
        validator_pipeline = ExcelValidationPipeline(config)
        return {
            'sow': sow_pipeline,
            'irl': irl_pipeline,
            'validator': validator_pipeline
        }
    except Exception as e:
        st.error(f"Failed to initialize pipelines: {e}")
        return None

def parse_sow_to_sections(sow_text: str) -> Dict[str, List[str]]:
    """Parse SOW text into sections with selectable procedures"""
    sections = {}
    
    # Find the DD SCOPE TABLE section
    table_start = sow_text.find("| Analysis Area | Detailed Procedures |")
    if table_start == -1:
        st.warning("Could not find DD SCOPE TABLE in SOW text")
        return sections
    
    # Find where the table ends (usually ends with a line of just pipes or empty)
    table_end = sow_text.find("\n\n", table_start + 200)  # Look for double newline after table start
    if table_end == -1:
        table_end = len(sow_text)
    
    # Extract just the table content
    table_content = sow_text[table_start:table_end]
    lines = table_content.split('\n')
    
    current_section = None
    current_procedures_text = ""
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if this is a section header (starts with | ** and contains **)
        if line.startswith('| **') and '**' in line[4:]:
            # Save previous section if exists
            if current_section and current_procedures_text:
                # Parse the procedures text to extract individual items
                procedures = []
                # Use regex to find all numbered items
                proc_matches = re.findall(r'(\d+)\.\s+([^0-9]+?)(?=\d+\.|$)', current_procedures_text)
                for num, proc_text in proc_matches:
                    procedures.append(proc_text.strip())
                if procedures:
                    sections[current_section] = procedures
            
            # Extract new section name
            section_match = re.search(r'\*\*(.*?)\*\*', line)
            if section_match:
                current_section = section_match.group(1)
                # Get the procedures text from this line (everything after the second |)
                parts = line.split('|')
                if len(parts) >= 3:
                    current_procedures_text = parts[2].strip()
        
        # Continue collecting procedures on following lines (lines that start with a number)
        elif current_section and line and (line[0].isdigit() or (not line.startswith('|') and not line.startswith('-'))):
            current_procedures_text += " " + line
        
        i += 1
    
    # Save the last section
    if current_section and current_procedures_text:
        procedures = []
        # Use regex to find all numbered items
        proc_matches = re.findall(r'(\d+)\.\s+([^0-9]+?)(?=\d+\.|$)', current_procedures_text)
        for num, proc_text in proc_matches:
            procedures.append(proc_text.strip())
        if procedures:
            sections[current_section] = procedures
    
    return sections

def reconstruct_sow_from_selections(original_sow: str, selected_procedures: Dict[str, List[str]]) -> str:
    """Reconstruct SOW based on user selections maintaining exact formatting"""
    if not selected_procedures:
        return None
    
    # Check if any procedures are selected
    total_selected = sum(len(procs) for procs in selected_procedures.values())
    if total_selected == 0:
        return None
    
    # Find the different sections of the original SOW
    lines = original_sow.split('\n')
    
    # Find key markers in the SOW
    header_end_idx = 0
    executive_start_idx = 0
    table_start_idx = 0
    table_header_idx = 0
    
    for i, line in enumerate(lines):
        if "EXECUTIVE SUMMARY" in line:
            executive_start_idx = i
        elif "**DD SCOPE TABLE**" in line:
            header_end_idx = i
        elif "| Analysis Area | Detailed Procedures |" in line:
            table_header_idx = i
            table_start_idx = i + 2  # Skip the header and separator line
            break
    
    # Build new SOW maintaining exact format
    new_sow_lines = []
    
    # Copy everything up to the DD SCOPE TABLE (including executive summary)
    new_sow_lines.extend(lines[:header_end_idx])
    
    # Add the DD SCOPE TABLE header
    new_sow_lines.append("**DD SCOPE TABLE**")
    new_sow_lines.append("=================")
    new_sow_lines.append("")
    
    # Add financial periods if present in original
    for i in range(header_end_idx, table_header_idx):
        if "Financial periods:" in lines[i]:
            new_sow_lines.append(lines[i])
            new_sow_lines.append("")
            break
    
    # Add table header
    new_sow_lines.append("| Analysis Area | Detailed Procedures |")
    new_sow_lines.append("|--------------|-------------------|")
    
    # Parse all sections from original SOW to maintain order
    all_sections = parse_sow_to_sections(original_sow)
    
    # Add selected sections and procedures in original order
    for section in all_sections.keys():
        if section in selected_procedures and selected_procedures[section]:
            # Build the procedures text maintaining the multi-line format
            procedures_text = "| **" + section + "** | "
            
            selected_procs = selected_procedures[section]
            # Get the original procedures to maintain numbering
            original_procs = all_sections[section]
            
            # Build numbered list with only selected procedures
            proc_lines = []
            proc_num = 1
            for orig_proc in original_procs:
                if orig_proc in selected_procs:
                    proc_lines.append(f"{proc_num}. {orig_proc}")
                    proc_num += 1
            
            # Format the procedures - first one on same line, rest on new lines
            if proc_lines:
                procedures_text += proc_lines[0]
                for proc in proc_lines[1:]:
                    procedures_text += "\n" + proc
                procedures_text += " |"
                
            new_sow_lines.append(procedures_text)
    
    return '\n'.join(new_sow_lines)

def find_latest_irl_file(company_name: str = None) -> Optional[str]:
    """Find the latest IRL Excel file based on version number"""
    import glob
    import re
    
    # Search patterns
    patterns = []
    if company_name:
        patterns.append(f"**/{company_name}_IRL_*.xlsx")
        patterns.append(f"**/{company_name}*IRL*.xlsx")
    patterns.append("**/*IRL*.xlsx")
    
    all_irl_files = []
    for pattern in patterns:
        all_irl_files.extend(glob.glob(pattern, recursive=True))
    
    if not all_irl_files:
        return None
    
    # Sort by version number if present
    versioned_files = []
    for file in all_irl_files:
        # Extract version number using regex
        version_match = re.search(r'_v(\d+)\.xlsx$', file)
        if version_match:
            version = int(version_match.group(1))
            versioned_files.append((file, version))
        else:
            # Files without version get version 0
            versioned_files.append((file, 0))
    
    # Sort by version number (highest first)
    versioned_files.sort(key=lambda x: x[1], reverse=True)
    
    # Return the file with highest version
    if versioned_files:
        return versioned_files[0][0]
    
    return None

def create_visualization_charts(validation_results: Dict) -> None:
    """Create visualization charts for validation results"""
    if not validation_results:
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart for validation status
        if 'summary' in validation_results:
            summary = validation_results['summary']
            fig = go.Figure(data=[go.Pie(
                labels=['Successful', 'Failed'],
                values=[summary.get('successful', 0), summary.get('failed', 0)],
                hole=.3,
                marker_colors=['#22c55e', '#ef4444']
            )])
            fig.update_layout(
                title="Validation Status Distribution",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Bar chart for file-wise validation
        if 'validation_results' in validation_results:
            files = []
            statuses = []
            for result in validation_results['validation_results']:
                files.append(result['file'][:20] + '...' if len(result['file']) > 20 else result['file'])
                status = result.get('validation', {}).get('status', 'unknown')
                statuses.append(1 if status == 'success' else 0)
            
            fig = go.Figure(data=[go.Bar(
                x=files,
                y=statuses,
                marker_color=['#22c55e' if s == 1 else '#ef4444' for s in statuses]
            )])
            fig.update_layout(
                title="File-wise Validation Results",
                xaxis_title="Files",
                yaxis_title="Status (1=Success, 0=Failed)",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)

def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown('<h1 class="main-header">📊 Zenalyst - Financial Due Diligence Platform</h1>', unsafe_allow_html=True)
    
    # Initialize pipelines
    if st.session_state.pipelines['sow'] is None:
        with st.spinner("Initializing processing pipelines..."):
            pipelines = initialize_pipelines()
            if pipelines:
                st.session_state.pipelines = pipelines
            else:
                st.error("Failed to initialize pipelines. Please refresh the page.")
                st.stop()
    
    # Sidebar for workflow navigation
    with st.sidebar:
        st.markdown("## 🔄 Workflow Navigation")
        st.markdown("---")
        
        # Progress indicator
        steps = ['📤 Upload/Generate SOW', '✅ Select Options', '📊 Generate IRL', '📁 Upload Files', '✔️ Validate']
        current_step = {
            'start': 0,
            'sow_uploaded': 1,
            'options_selected': 2,
            'irl_generated': 3,
            'files_uploaded': 4,
            'validated': 5
        }.get(st.session_state.workflow_state, 0)
        
        for i, step in enumerate(steps):
            if i < current_step:
                st.success(f"✅ {step}")
            elif i == current_step:
                st.info(f"▶️ {step}")
            else:
                st.text(f"⏸️ {step}")
        
        st.markdown("---")
        
        # Reset button
        if st.button("🔄 Reset Workflow", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key != 'pipelines':
                    del st.session_state[key]
            st.session_state.workflow_state = 'start'
            st.rerun()
    
    # Main content area
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📤 SOW Upload", "✅ Option Selection", "📊 IRL Generation", "📁 File Upload & Validation", "📈 Results"])
    
    # Tab 1: SOW Upload
    with tab1:
        st.markdown('<h2 class="step-header">Step 1: Generate or Upload SOW</h2>', unsafe_allow_html=True)
        
        # Option to choose between generating new SOW or uploading existing
        sow_option = st.radio(
            "Choose how to provide SOW:",
            ["📝 Generate new SOW from documents", "📤 Upload existing SOW file"],
            help="Generate a new SOW from your documents or upload an existing SOW file"
        )
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if sow_option == "📝 Generate new SOW from documents":
                st.markdown('<div class="info-box">', unsafe_allow_html=True)
                st.markdown("### 📋 Generate SOW from Documents")
                st.markdown("""
                1. Upload your company documents (PDF, Excel, etc.)
                2. System will analyze and generate a comprehensive SOW
                3. The generated SOW will contain all standard due diligence sections
                4. You can then customize the scope in the next step
                """)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Input fields for SOW generation
                investor_id = st.text_input("Investor ID", value="INV001", key="sow_investor")
                investee_id = st.text_input("Investee/Company ID", value="ABC_Company", key="sow_investee")
                
                # Multiple file uploader for documents
                uploaded_docs = st.file_uploader(
                    "Upload documents for SOW generation",
                    type=['pdf', 'xlsx', 'xls', 'docx', 'txt'],
                    accept_multiple_files=True,
                    help="Upload company documents, financial statements, etc."
                )
                
                additional_context = st.text_area(
                    "Additional Context (Optional)",
                    placeholder="Enter any additional information about the due diligence requirements...",
                    height=100
                )
                
                if uploaded_docs and st.button("🚀 Generate SOW", type="primary", use_container_width=True):
                    with st.spinner("Analyzing documents and generating SOW..."):
                        try:
                            sow_pipeline = st.session_state.pipelines['sow']
                            
                            # Process all uploaded documents
                            consolidated_text = ""
                            temp_files = []
                            
                            for doc in uploaded_docs:
                                # Save uploaded file temporarily
                                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(doc.name).suffix) as tmp_file:
                                    tmp_file.write(doc.getbuffer())
                                    temp_files.append(tmp_file.name)
                                    
                                    # Extract text based on file type
                                    if doc.type == "application/pdf":
                                        extracted_text, used_ocr = sow_pipeline.ocr_handler.extract_text_from_pdf(tmp_file.name)
                                        if extracted_text:
                                            extraction_method = "OCR" if used_ocr else "PyPDF2"
                                            consolidated_text += f"\n\n--- Document: {doc.name} ---\n"
                                            consolidated_text += f"--- Extraction Method: {extraction_method} ---\n"
                                            consolidated_text += extracted_text
                                            st.info(f"📄 Extracted {len(extracted_text)} characters from {doc.name} using {extraction_method}")
                                    elif doc.type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel"]:
                                        # Handle Excel files
                                        df = pd.read_excel(tmp_file.name)
                                        consolidated_text += f"\n\n--- Document: {doc.name} ---\n"
                                        consolidated_text += df.to_string()
                                    elif doc.type == "text/plain":
                                        text_content = doc.getvalue().decode("utf-8")
                                        consolidated_text += f"\n\n--- Document: {doc.name} ---\n"
                                        consolidated_text += text_content
                                    else:
                                        # Try to read as text
                                        try:
                                            with open(tmp_file.name, 'r', encoding='utf-8', errors='ignore') as f:
                                                consolidated_text += f"\n\n--- Document: {doc.name} ---\n"
                                                consolidated_text += f.read()
                                        except:
                                            st.warning(f"Could not process {doc.name}")
                            
                            # Generate SOW using the pipeline
                            if not consolidated_text:
                                consolidated_text = f"Generate due diligence scope for {investee_id} investment by {investor_id}. {additional_context}"
                            
                            # Extract company name
                            company_name = investee_id
                            if consolidated_text:
                                try:
                                    extracted_company = sow_pipeline.claude_analyzer.extract_company_name(consolidated_text[:3000])
                                    if extracted_company and extracted_company.lower() not in ['unknown', 'not found', 'n/a']:
                                        company_name = extracted_company
                                except:
                                    pass
                            
                            # Analyze financial content to get requirements
                            requirements = sow_pipeline.analyze_financial_content_for_requirements(
                                consolidated_text,
                                company_name
                            )
                            
                            # Generate scope using the pipeline's method
                            sow_content = sow_pipeline._generate_strict_dd_scope(requirements)
                            
                            # Save the generated SOW
                            output_file = sow_pipeline._save_versioned_output(company_name, sow_content)
                            
                            if sow_content:
                                st.session_state.sow_content = sow_content
                                st.session_state.sow_sections = parse_sow_to_sections(sow_content)
                                st.session_state.original_sow_filename = f"{company_name}_SOW"
                                
                                # Auto-select all procedures when generating new SOW
                                st.session_state.selected_procedures = {}
                                for section, procedures in st.session_state.sow_sections.items():
                                    st.session_state.selected_procedures[section] = procedures.copy()
                                
                                # Set customized_sow to the full generated SOW initially
                                st.session_state.customized_sow = sow_content
                                
                                # Auto-save the customized SOW with "selected_" prefix
                                selected_filename = f"selected_{company_name}_SOW_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                                selected_filepath = os.path.join(os.path.dirname(output_file), selected_filename)
                                with open(selected_filepath, 'w', encoding='utf-8') as f:
                                    f.write(sow_content)
                                st.session_state.customized_sow_path = selected_filepath
                                
                                st.session_state.workflow_state = 'options_selected'  # Skip to options_selected since all are pre-selected
                                
                                st.markdown('<div class="success-box">', unsafe_allow_html=True)
                                st.success(f"✅ Successfully generated SOW for {company_name}")
                                st.markdown(f"📊 Found {len(st.session_state.sow_sections)} analysis sections")
                                st.markdown(f"📁 Original saved to: {output_file}")
                                st.markdown(f"📁 Selected SOW saved to: {selected_filepath}")
                                st.markdown(f"✅ All procedures auto-selected - you can customize in the next tab")
                                st.markdown('</div>', unsafe_allow_html=True)
                                
                                # Display generated SOW preview
                                with st.expander("View Generated SOW"):
                                    st.text(sow_content[:3000] + "..." if len(sow_content) > 3000 else sow_content)
                                
                                # Download button for generated SOW
                                st.download_button(
                                    label="📥 Download Generated SOW",
                                    data=sow_content,
                                    file_name=f"{company_name}_SOW_{datetime.now().strftime('%Y%m%d')}.txt",
                                    mime="text/plain"
                                )
                            else:
                                st.error("Failed to generate SOW content")
                            
                        except Exception as e:
                            st.error(f"Error generating SOW: {str(e)}")
                        finally:
                            # Cleanup temp files
                            for temp_file in temp_files:
                                if os.path.exists(temp_file):
                                    os.remove(temp_file)
                
            else:  # Upload existing SOW file
                st.markdown('<div class="info-box">', unsafe_allow_html=True)
                st.markdown("### 📋 Upload Existing SOW")
                st.markdown("""
                1. Upload your existing Statement of Work (SOW) document
                2. Supported formats: TXT, PDF, DOCX
                3. The system will parse and extract analysis sections
                4. You'll be able to customize the scope in the next step
                """)
                st.markdown('</div>', unsafe_allow_html=True)
                
                uploaded_file = st.file_uploader(
                    "Choose SOW file",
                    type=['txt', 'pdf', 'docx'],
                    help="Upload the SOW document to parse"
                )
                
                if uploaded_file:
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                        tmp_file.write(uploaded_file.getbuffer())
                        tmp_path = tmp_file.name
                    
                    # Process the file
                    with st.spinner("Processing SOW document..."):
                        try:
                            # Read the file content
                            if uploaded_file.type == "text/plain":
                                sow_content = uploaded_file.getvalue().decode("utf-8")
                            else:
                                # Use OCR handler for PDFs
                                sow_pipeline = st.session_state.pipelines['sow']
                                if uploaded_file.type == "application/pdf":
                                    sow_content, _ = sow_pipeline.ocr_handler.extract_text_from_pdf(tmp_path)
                                else:
                                    with open(tmp_path, 'r', encoding='utf-8', errors='ignore') as f:
                                        sow_content = f.read()
                            
                            if sow_content:
                                st.session_state.sow_content = sow_content
                                st.session_state.sow_sections = parse_sow_to_sections(sow_content)
                                st.session_state.workflow_state = 'sow_uploaded'
                                
                                # Store original filename (without extension)
                                original_name = Path(uploaded_file.name).stem
                                st.session_state.original_sow_filename = original_name
                                
                                st.markdown('<div class="success-box">', unsafe_allow_html=True)
                                st.success(f"✅ Successfully loaded SOW: {uploaded_file.name}")
                                st.markdown(f"📊 Found {len(st.session_state.sow_sections)} analysis sections")
                                st.markdown('</div>', unsafe_allow_html=True)
                                
                                # Display parsed sections summary
                                with st.expander("View Parsed Sections"):
                                    for section, procedures in st.session_state.sow_sections.items():
                                        st.markdown(f"**{section}**: {len(procedures)} procedures")
                            else:
                                st.error("Could not extract content from the uploaded file")
                        
                        except Exception as e:
                            st.error(f"Error processing file: {str(e)}")
                        finally:
                            # Cleanup temp file
                            if os.path.exists(tmp_path):
                                os.remove(tmp_path)
        
        with col2:
            st.markdown("### 📊 Quick Stats")
            if st.session_state.sow_sections:
                total_sections = len(st.session_state.sow_sections)
                total_procedures = sum(len(procs) for procs in st.session_state.sow_sections.values())
                
                st.metric("Total Sections", total_sections)
                st.metric("Total Procedures", total_procedures)
                
                # Mini chart of procedures per section
                section_names = list(st.session_state.sow_sections.keys())[:5]
                proc_counts = [len(st.session_state.sow_sections[s]) for s in section_names]
                
                fig = go.Figure(data=[go.Bar(
                    x=proc_counts,
                    y=section_names,
                    orientation='h',
                    marker_color='#3b82f6'
                )])
                fig.update_layout(
                    title="Top 5 Sections",
                    height=200,
                    margin=dict(l=0, r=0, t=30, b=0),
                    xaxis_title="Procedures",
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # Tab 2: Option Selection
    with tab2:
        st.markdown('<h2 class="step-header">Step 2: Customize Analysis Scope</h2>', unsafe_allow_html=True)
        
        if not st.session_state.sow_sections:
            st.warning("⚠️ Please upload a SOW document first")
        else:
            # Check if coming from generated SOW
            if st.session_state.workflow_state == 'options_selected' and st.session_state.customized_sow:
                st.markdown('<div class="success-box">', unsafe_allow_html=True)
                st.success("✅ SOW is ready! All procedures are selected by default.")
                st.info("💡 You can proceed directly to IRL Generation (Tab 3) or customize the selection below.")
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            st.markdown("### 📋 Instructions")
            st.markdown("""
            - Select the procedures you want to include for each analysis section
            - At least one procedure must be selected from any section
            - Sections with no selected procedures will be excluded from the final SOW
            """)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Selection interface
            selected_procedures = {}
            
            # Add select all/none buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✅ Select All", use_container_width=True):
                    for section, procedures in st.session_state.sow_sections.items():
                        st.session_state.selected_procedures[section] = procedures.copy()
                    st.rerun()
            with col2:
                if st.button("❌ Clear All", use_container_width=True):
                    st.session_state.selected_procedures = {}
                    st.rerun()
            with col3:
                total_selected = sum(len(st.session_state.selected_procedures.get(s, [])) 
                                   for s in st.session_state.sow_sections.keys())
                st.metric("Selected Procedures", total_selected)
            
            st.markdown("---")
            
            # Create expandable sections for each analysis area
            for section, procedures in st.session_state.sow_sections.items():
                with st.expander(f"📂 **{section}** ({len(procedures)} procedures)"):
                    st.markdown(f'<div class="analysis-section">', unsafe_allow_html=True)
                    
                    # Section select all/none
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Select All", key=f"all_{section}"):
                            if section not in st.session_state.selected_procedures:
                                st.session_state.selected_procedures[section] = []
                            st.session_state.selected_procedures[section] = procedures.copy()
                            st.rerun()
                    with col2:
                        if st.button(f"Clear", key=f"none_{section}"):
                            if section in st.session_state.selected_procedures:
                                st.session_state.selected_procedures[section] = []
                            st.rerun()
                    
                    st.markdown("---")
                    
                    # Initialize section in selected_procedures if not exists
                    if section not in st.session_state.selected_procedures:
                        st.session_state.selected_procedures[section] = []
                    
                    # Checkboxes for each procedure
                    for i, procedure in enumerate(procedures):
                        is_selected = procedure in st.session_state.selected_procedures.get(section, [])
                        if st.checkbox(
                            f"{i+1}. {procedure}",
                            value=is_selected,
                            key=f"{section}_{i}"
                        ):
                            if section not in st.session_state.selected_procedures:
                                st.session_state.selected_procedures[section] = []
                            if procedure not in st.session_state.selected_procedures[section]:
                                st.session_state.selected_procedures[section].append(procedure)
                        else:
                            if section in st.session_state.selected_procedures:
                                if procedure in st.session_state.selected_procedures[section]:
                                    st.session_state.selected_procedures[section].remove(procedure)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
            
            # Generate customized SOW button
            st.markdown("---")
            if st.button("🚀 Update Customized SOW", type="primary", use_container_width=True):
                # Validate selections
                total_selected = sum(len(procs) for procs in st.session_state.selected_procedures.values())
                
                if total_selected == 0:
                    st.error("❌ Please select at least one procedure from any analysis section")
                else:
                    # Clean up empty sections
                    cleaned_selections = {k: v for k, v in st.session_state.selected_procedures.items() if v}
                    
                    # Reconstruct SOW
                    new_sow = reconstruct_sow_from_selections(
                        st.session_state.sow_content,
                        cleaned_selections
                    )
                    
                    if new_sow:
                        st.session_state.customized_sow = new_sow
                        st.session_state.workflow_state = 'options_selected'
                        
                        # Auto-save the customized SOW with "selected_" prefix
                        base_name = st.session_state.original_sow_filename or "SOW"
                        selected_filename = f"selected_{base_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                        
                        # Create output directory if it doesn't exist
                        output_dir = "output"
                        if not os.path.exists(output_dir):
                            os.makedirs(output_dir)
                        
                        selected_filepath = os.path.join(output_dir, selected_filename)
                        with open(selected_filepath, 'w', encoding='utf-8') as f:
                            f.write(new_sow)
                        st.session_state.customized_sow_path = selected_filepath
                        
                        st.markdown('<div class="success-box">', unsafe_allow_html=True)
                        st.success(f"✅ Updated customized SOW with {len(cleaned_selections)} sections and {total_selected} procedures")
                        st.markdown(f"📁 Auto-saved to: {selected_filepath}")
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Show preview
                        with st.expander("Preview Customized SOW"):
                            st.text(new_sow[:2000] + "..." if len(new_sow) > 2000 else new_sow)
                        
                        # Add download button for customized SOW
                        st.download_button(
                            label="📥 Download Customized SOW",
                            data=new_sow,
                            file_name=selected_filename,
                            mime="text/plain"
                        )
                    else:
                        st.error("Failed to generate customized SOW")
    
    # Tab 3: IRL Generation
    with tab3:
        st.markdown('<h2 class="step-header">Step 3: Generate IRL Excel</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            st.markdown("### 📋 IRL Generation")
            st.markdown("""
            The Information Request List (IRL) will be generated based on your SOW.
            This Excel file will contain:
            - Detailed information requirements
            - Document requests
            - Data requirements for validation
            """)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Check if customized SOW is available
            if st.session_state.customized_sow_path and os.path.exists(st.session_state.customized_sow_path):
                st.markdown('<div class="success-box">', unsafe_allow_html=True)
                st.success(f"✅ Using customized SOW from: {os.path.basename(st.session_state.customized_sow_path)}")
                
                # Show preview of the customized SOW
                with st.expander("Preview Customized SOW"):
                    with open(st.session_state.customized_sow_path, 'r', encoding='utf-8') as f:
                        sow_preview = f.read()
                        st.text(sow_preview[:2000] + "..." if len(sow_preview) > 2000 else sow_preview)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Input fields for IRL generation
                investor_id = st.text_input("Investor ID", value="INV001", help="Enter the investor identifier")
                investee_id = st.text_input("Investee ID", value="ABC_Company", help="Enter the investee/target company identifier")
                
                if st.button("📊 Generate IRL Excel", type="primary", use_container_width=True):
                    with st.spinner("Generating IRL Excel..."):
                        try:
                            # Use the already saved customized SOW file
                            irl_pipeline = st.session_state.pipelines['irl']
                            result = irl_pipeline.process_sow_to_irl(st.session_state.customized_sow_path)
                            
                            if result['status'] == 'success':
                                st.session_state.irl_excel_path = result['irl_excel_file']
                                st.session_state.workflow_state = 'irl_generated'
                                
                                st.markdown('<div class="success-box">', unsafe_allow_html=True)
                                st.success("✅ IRL Excel generated successfully!")
                                
                                # Provide download button
                                with open(st.session_state.irl_excel_path, 'rb') as f:
                                    excel_data = f.read()
                                
                                st.download_button(
                                    label="📥 Download IRL Excel",
                                    data=excel_data,
                                    file_name=f"{investee_id}_IRL_{datetime.now().strftime('%Y%m%d')}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                                st.markdown('</div>', unsafe_allow_html=True)
                                
                                # Show preview of IRL
                                with st.expander("Preview IRL Content"):
                                    df = pd.read_excel(st.session_state.irl_excel_path)
                                    st.dataframe(df.head(10), use_container_width=True)
                            else:
                                st.error(f"Failed to generate IRL: {result.get('error', 'Unknown error')}")
                            
                        except Exception as e:
                            st.error(f"Error generating IRL: {str(e)}")
            else:
                # No customized SOW available
                st.markdown('<div class="warning-box">', unsafe_allow_html=True)
                st.warning("⚠️ No customized SOW file found.")
                st.info("Please complete Steps 1 and 2 to generate a customized SOW first.")
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Provide option to upload SOW file directly
                st.markdown("### 📤 Or Upload SOW File Directly")
                uploaded_sow = st.file_uploader(
                    "Upload SOW file for IRL generation",
                    type=['txt'],
                    help="Upload a SOW text file to generate IRL"
                )
                
                if uploaded_sow:
                    # Save the uploaded file
                    output_dir = "output"
                    if not os.path.exists(output_dir):
                        os.makedirs(output_dir)
                    
                    uploaded_path = os.path.join(output_dir, f"uploaded_{uploaded_sow.name}")
                    with open(uploaded_path, 'wb') as f:
                        f.write(uploaded_sow.getbuffer())
                    
                    st.session_state.customized_sow_path = uploaded_path
                    st.success(f"✅ Uploaded SOW: {uploaded_sow.name}")
                    st.info("Please click the button above to refresh and generate IRL")
                    st.rerun()
            
            with col2:
                st.markdown("### 📊 IRL Status")
                if st.session_state.irl_excel_path and os.path.exists(st.session_state.irl_excel_path):
                    st.success("✅ IRL Available")
                    
                    # Show IRL statistics
                    try:
                        df = pd.read_excel(st.session_state.irl_excel_path)
                        st.metric("Total Requirements", len(df))
                        
                        # Count by section if available
                        if 'Section' in df.columns:
                            section_counts = df['Section'].value_counts()
                            fig = go.Figure(data=[go.Pie(
                                labels=section_counts.index[:5],
                                values=section_counts.values[:5],
                                hole=.3
                            )])
                            fig.update_layout(
                                title="Top 5 Sections",
                                height=250,
                                margin=dict(l=0, r=0, t=30, b=0)
                            )
                            st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.warning(f"Could not load IRL statistics: {e}")
                else:
                    st.info("⏸️ IRL not generated yet")
    
    # Tab 4: File Upload & Validation
    with tab4:
        st.markdown('<h2 class="step-header">Step 4: Upload Files for Validation</h2>', unsafe_allow_html=True)
        
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("### 📋 Validation Instructions")
        st.markdown("""
        1. The system will use the IRL Excel to understand validation requirements
        2. Upload the Excel files to validate against IRL specifications
        3. You'll receive a detailed validation report
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # IRL File Selection/Detection
        st.markdown("### 📊 IRL File Selection")
        
        irl_file_path = None
        
        # Try to auto-detect IRL file
        if st.session_state.irl_excel_path and os.path.exists(st.session_state.irl_excel_path):
            # Use the IRL generated in previous step
            irl_file_path = st.session_state.irl_excel_path
            st.success(f"✅ Using IRL from Step 3: {os.path.basename(irl_file_path)}")
        else:
            # Try to find the latest IRL file
            company_name = st.session_state.original_sow_filename
            if company_name and "SOW" in company_name:
                company_name = company_name.replace("_SOW", "").replace("SOW", "")
            
            latest_irl = find_latest_irl_file(company_name)
            
            if latest_irl:
                irl_file_path = latest_irl
                st.success(f"✅ Auto-detected latest IRL: {os.path.basename(latest_irl)}")
                
                # Show version info if available
                import re
                version_match = re.search(r'_v(\d+)\.xlsx$', latest_irl)
                if version_match:
                    st.info(f"Version: v{version_match.group(1)}")
        
        # Option to upload different IRL file
        use_different_irl = st.checkbox("📤 Upload a different IRL file", help="Check this to upload a different IRL file")
        
        if use_different_irl:
            uploaded_irl = st.file_uploader(
                "Upload IRL Excel file",
                type=['xlsx', 'xls'],
                help="Upload the IRL Excel file containing validation requirements"
            )
            
            if uploaded_irl:
                # Save the uploaded IRL
                output_dir = "output"
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                
                irl_path = os.path.join(output_dir, f"uploaded_irl_{uploaded_irl.name}")
                with open(irl_path, 'wb') as f:
                    f.write(uploaded_irl.getbuffer())
                
                irl_file_path = irl_path
                st.success(f"✅ Using uploaded IRL: {uploaded_irl.name}")
        
        # Show IRL preview if available
        if irl_file_path and os.path.exists(irl_file_path):
            with st.expander("Preview IRL Requirements"):
                try:
                    irl_df = pd.read_excel(irl_file_path)
                    st.dataframe(irl_df.head(10), use_container_width=True)
                    st.info(f"Total requirements: {len(irl_df)}")
                except Exception as e:
                    st.error(f"Could not read IRL file: {e}")
        
        st.markdown("---")
        
        # File upload section
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 📁 Upload Files for Validation")
            
            # Multiple file uploader
            uploaded_files = st.file_uploader(
                "Choose Excel files to validate",
                type=['xlsx', 'xls', 'csv'],
                accept_multiple_files=True,
                help="Upload the Excel files that need to be validated against IRL requirements"
            )
            
            if uploaded_files:
                st.markdown(f"📎 {len(uploaded_files)} file(s) uploaded")
                
                # Display uploaded files
                for file in uploaded_files:
                    col_file, col_size = st.columns([3, 1])
                    with col_file:
                        st.text(f"📄 {file.name}")
                    with col_size:
                        st.text(f"{file.size / 1024:.1f} KB")
                
                # Validation button
                if st.button("✔️ Validate Files Against IRL", type="primary", use_container_width=True):
                    if not irl_file_path:
                        st.error("❌ No IRL file found. Please upload an IRL file or complete Step 3 to generate one.")
                    else:
                        with st.spinner(f"Validating files against IRL requirements..."):
                            try:
                                # Parse IRL requirements first
                                irl_requirements = {}
                                try:
                                    irl_df = pd.read_excel(irl_file_path)
                                    # Extract requirements from IRL Excel
                                    irl_requirements = {
                                        'file': os.path.basename(irl_file_path),
                                        'total_requirements': len(irl_df),
                                        'sections': [],
                                        'requirements': []
                                    }
                                    
                                    # Parse IRL structure
                                    for idx, row in irl_df.iterrows():
                                        requirement = {}
                                        # Try different column name variations
                                        for col in ['Information Requirement', 'Info Requirement', 'Requirement', 'Description']:
                                            if col in irl_df.columns and pd.notna(row.get(col)):
                                                requirement['description'] = str(row.get(col))
                                                break
                                        
                                        for col in ['Section', 'Category', 'Area']:
                                            if col in irl_df.columns and pd.notna(row.get(col)):
                                                requirement['section'] = str(row.get(col))
                                                if requirement['section'] not in irl_requirements['sections']:
                                                    irl_requirements['sections'].append(requirement['section'])
                                                break
                                        
                                        if requirement:
                                            requirement['id'] = idx + 1
                                            irl_requirements['requirements'].append(requirement)
                                    
                                    st.info(f"📊 Loaded {len(irl_requirements['requirements'])} requirements from IRL")
                                    
                                except Exception as e:
                                    st.warning(f"Could not parse IRL requirements: {e}")
                                    irl_requirements = None
                                
                                # Create persistent temp directory (not auto-deleted)
                                import time
                                temp_dir = os.path.join(tempfile.gettempdir(), f"zenalyst_validation_{int(time.time())}")
                                os.makedirs(temp_dir, exist_ok=True)
                                
                                try:
                                    temp_paths = []
                                    
                                    # Save uploaded files with unique names to avoid conflicts
                                    for i, file in enumerate(uploaded_files):
                                        # Add index to filename to ensure uniqueness
                                        safe_name = f"{i}_{file.name}"
                                        file_path = os.path.join(temp_dir, safe_name)
                                        
                                        # Write file content
                                        try:
                                            with open(file_path, 'wb') as f:
                                                f.write(file.getbuffer())
                                            temp_paths.append((file_path, file.name))  # Store both paths
                                        except Exception as e:
                                            st.warning(f"Could not save {file.name}: {e}")
                                            continue
                                    
                                    # Perform validation
                                    validator = st.session_state.pipelines['validator']
                                    validation_results = {
                                        'irl_file': os.path.basename(irl_file_path) if irl_file_path else None,
                                        'irl_requirements': irl_requirements,
                                        'validation_results': [],
                                        'summary': {
                                            'total_files': len(uploaded_files),
                                            'successful': 0,
                                            'failed': 0,
                                            'irl_coverage': 0
                                        }
                                    }
                                    
                                    for file_path, original_name in temp_paths:
                                        try:
                                            # Process file with proper error handling
                                            result = None
                                            try:
                                                result = validator.process_file(file_path)
                                            except PermissionError as pe:
                                                # If file is locked, try copying to a new temp file
                                                import uuid
                                                new_path = os.path.join(temp_dir, f"copy_{uuid.uuid4().hex}_{os.path.basename(file_path)}")
                                                import shutil
                                                shutil.copy2(file_path, new_path)
                                                result = validator.process_file(new_path)
                                            except ZeroDivisionError as zde:
                                                # Handle division by zero errors from validator
                                                st.warning(f"⚠️ File {original_name} appears to be empty or has no valid data")
                                                result = {
                                                    'status': 'warning',
                                                    'message': 'File is empty or contains no processable data',
                                                    'error': 'Empty or invalid data detected'
                                                }
                                            
                                            # Add IRL context to result
                                            if irl_requirements:
                                                result['irl_context'] = {
                                                    'total_requirements': irl_requirements['total_requirements'],
                                                    'sections': irl_requirements['sections']
                                                }
                                            
                                            validation_results['validation_results'].append({
                                                'file': original_name,
                                                'validation': result
                                            })
                                            
                                            if result.get('status') == 'success':
                                                validation_results['summary']['successful'] += 1
                                            else:
                                                validation_results['summary']['failed'] += 1
                                        except Exception as e:
                                            validation_results['validation_results'].append({
                                                'file': original_name,
                                                'validation': {
                                                    'status': 'error',
                                                    'error': str(e)
                                                }
                                            })
                                            validation_results['summary']['failed'] += 1
                                    
                                    # Calculate IRL coverage if applicable
                                    if irl_requirements and validation_results['summary']['successful'] > 0:
                                        req_count = len(irl_requirements.get('requirements', []))
                                        if req_count > 0:
                                            validation_results['summary']['irl_coverage'] = (
                                                validation_results['summary']['successful'] / req_count * 100
                                            )
                                        else:
                                            validation_results['summary']['irl_coverage'] = 0
                                    
                                    st.session_state.validation_results = validation_results
                                    st.session_state.workflow_state = 'validated'
                                    
                                    st.markdown('<div class="success-box">', unsafe_allow_html=True)
                                    st.success("✅ Validation completed!")
                                    st.markdown(f"📊 IRL File: {validation_results['irl_file']}")
                                    st.markdown(f"✅ Successful: {validation_results['summary']['successful']}")
                                    st.markdown(f"❌ Failed: {validation_results['summary']['failed']}")
                                    if irl_requirements:
                                        st.markdown(f"📈 IRL Coverage: {validation_results['summary']['irl_coverage']:.1f}%")
                                    st.markdown('</div>', unsafe_allow_html=True)
                                    
                                finally:
                                    # Clean up temp directory with retry logic
                                    import time
                                    for attempt in range(3):
                                        try:
                                            # Give Windows time to release file handles
                                            time.sleep(0.5)
                                            import shutil
                                            if os.path.exists(temp_dir):
                                                shutil.rmtree(temp_dir, ignore_errors=True)
                                            break
                                        except:
                                            if attempt == 2:  # Last attempt
                                                # Just ignore if we can't delete - Windows will clean it up eventually
                                                pass
                                    
                            except Exception as e:
                                st.error(f"Validation error: {str(e)}")
            
            with col2:
                st.markdown("### 📊 Validation Guide")
                st.info("""
                **What is validated:**
                - Data completeness
                - Format compliance
                - Required fields
                - Data quality
                - IRL requirements coverage
                """)
                
                if st.session_state.validation_results:
                    st.markdown("### ✅ Last Validation")
                    summary = st.session_state.validation_results['summary']
                    st.metric("Success Rate", 
                             f"{(summary['successful'] / summary['total_files'] * 100):.0f}%" 
                             if summary['total_files'] > 0 else "0%")
    
    # Tab 5: Results
    with tab5:
        st.markdown('<h2 class="step-header">Step 5: Validation Results & Reports</h2>', unsafe_allow_html=True)
        
        if not st.session_state.validation_results:
            st.warning("⚠️ No validation results available. Please complete the validation process first.")
        else:
            # IRL Information
            if st.session_state.validation_results.get('irl_file'):
                st.markdown('<div class="info-box">', unsafe_allow_html=True)
                st.markdown(f"### 📊 IRL Used for Validation")
                st.markdown(f"**File:** {st.session_state.validation_results['irl_file']}")
                
                if st.session_state.validation_results.get('irl_requirements'):
                    irl_req = st.session_state.validation_results['irl_requirements']
                    st.markdown(f"**Total Requirements:** {irl_req.get('total_requirements', 'N/A')}")
                    if irl_req.get('sections'):
                        st.markdown(f"**Sections:** {', '.join(irl_req['sections'][:5])}" + 
                                  (" ..." if len(irl_req['sections']) > 5 else ""))
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Summary metrics
            col1, col2, col3, col4, col5 = st.columns(5)
            summary = st.session_state.validation_results['summary']
            
            with col1:
                st.metric("Total Files", summary['total_files'])
            with col2:
                st.metric("Successful", summary['successful'], delta=None, delta_color="normal")
            with col3:
                st.metric("Failed", summary['failed'], delta=None, delta_color="inverse")
            with col4:
                success_rate = (summary['successful'] / summary['total_files'] * 100) if summary['total_files'] > 0 else 0
                st.metric("Success Rate", f"{success_rate:.1f}%")
            with col5:
                if summary.get('irl_coverage', 0) > 0:
                    st.metric("IRL Coverage", f"{summary['irl_coverage']:.1f}%")
            
            st.markdown("---")
            
            # Visualization charts
            create_visualization_charts(st.session_state.validation_results)
            
            st.markdown("---")
            
            # Detailed results
            st.markdown("### 📋 Detailed Validation Results")
            
            for result in st.session_state.validation_results['validation_results']:
                file_name = result['file']
                validation = result['validation']
                status = validation.get('status', 'unknown')
                
                # Create expander for each file
                with st.expander(f"📄 {file_name} - {'✅ Success' if status == 'success' else '❌ Failed'}"):
                    if status == 'success':
                        st.success("✅ Validation passed")
                        
                        # Show validation details if available
                        if 'summary' in validation:
                            st.markdown("**Summary:**")
                            st.json(validation['summary'])
                        
                        if 'data_quality' in validation:
                            st.markdown("**Data Quality Metrics:**")
                            quality_df = pd.DataFrame([validation['data_quality']])
                            st.dataframe(quality_df, use_container_width=True)
                    else:
                        st.error(f"❌ Validation failed: {validation.get('error', 'Unknown error')}")
                        
                        # Show error details
                        if 'details' in validation:
                            st.markdown("**Error Details:**")
                            st.json(validation['details'])
            
            # Export results
            st.markdown("---")
            st.markdown("### 📥 Export Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # JSON export
                json_str = json.dumps(st.session_state.validation_results, indent=2, default=str)
                st.download_button(
                    label="📄 Download JSON Report",
                    data=json_str,
                    file_name=f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            with col2:
                # CSV export
                if st.session_state.validation_results['validation_results']:
                    # Convert to DataFrame for CSV export
                    rows = []
                    for result in st.session_state.validation_results['validation_results']:
                        rows.append({
                            'File': result['file'],
                            'Status': result['validation'].get('status', 'unknown'),
                            'Error': result['validation'].get('error', ''),
                            'Timestamp': datetime.now().isoformat()
                        })
                    
                    df = pd.DataFrame(rows)
                    csv = df.to_csv(index=False)
                    
                    st.download_button(
                        label="📊 Download CSV Report",
                        data=csv,
                        file_name=f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #6b7280; padding: 1rem;'>
            <p>Zenalyst Financial Due Diligence Platform v1.0</p>
            <p>© 2024 - All Rights Reserved</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()