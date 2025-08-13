#!/usr/bin/env python3
"""
Zenalyst Unified API System
============================
Main API file integrating SOW generation, IRL processing, and validation workflows.

API Endpoints:
1. /sow/generate - Generate SOW text from investor/investee data and documents
2. /sow/to_excel - Convert SOW text to Excel format
3. /irl/validate - Validate Excel files against IRL requirements
"""

from flask import Flask, request, jsonify, send_file
import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import pandas as pd
from datetime import datetime
import traceback
from IRL.irl_dd_pipeline import logger

# Import existing modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'SOW'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'IRL'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Validator'))

try:
    from SOW.dynamic_dd_pipeline import DynamicDueDiligencePipeline
    from IRL.irl_dd_pipeline import IRLDueDiligencePipeline
    from Validator.pipeline import ExcelValidationPipeline
    from Validator.config import PipelineConfig
except ImportError as e:
    logger.error(f"Import error: {e}")
    # Fallback imports with absolute paths
    import importlib.util
    
    spec = importlib.util.spec_from_file_location("dynamic_dd_pipeline", 
                                                   os.path.join(os.path.dirname(__file__), 'SOW', 'dynamic_dd_pipeline.py'))
    dynamic_dd_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dynamic_dd_module)
    DynamicDueDiligencePipeline = dynamic_dd_module.DynamicDueDiligencePipeline
    
    spec = importlib.util.spec_from_file_location("irl_dd_pipeline",
                                                   os.path.join(os.path.dirname(__file__), 'IRL', 'irl_dd_pipeline.py'))
    irl_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(irl_module)
    IRLDueDiligencePipeline = irl_module.IRLDueDiligencePipeline
    
    spec = importlib.util.spec_from_file_location("pipeline",
                                                   os.path.join(os.path.dirname(__file__), 'Validator', 'pipeline.py'))
    validator_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator_module)
    ExcelValidationPipeline = validator_module.ExcelValidationPipeline
    
    spec = importlib.util.spec_from_file_location("config",
                                                   os.path.join(os.path.dirname(__file__), 'Validator', 'config.py'))
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)
    PipelineConfig = config_module.PipelineConfig

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize pipelines
sow_pipeline = None
irl_pipeline = None
validator_pipeline = None

def initialize_pipelines():
    """Initialize all processing pipelines"""
    global sow_pipeline, irl_pipeline, validator_pipeline
    
    try:
        sow_pipeline = DynamicDueDiligencePipeline()
        irl_pipeline = IRLDueDiligencePipeline()
        
        # Initialize validator with default config
        config = PipelineConfig()
        validator_pipeline = ExcelValidationPipeline(config)
        
        logger.info("All pipelines initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize pipelines: {e}")
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'pipelines': {
            'sow': sow_pipeline is not None,
            'irl': irl_pipeline is not None,
            'validator': validator_pipeline is not None
        }
    })

@app.route('/sow/generate', methods=['POST'])
def generate_sow():
    """
    Generate SOW text from investor/investee data and documents
    
    Expected JSON payload:
    {
        "investor_id": "string",
        "investee_id": "string",
        "documents": [
            {
                "name": "filename",
                "type": "pdf/excel/txt",
                "path": "file_path_or_base64_content"
            }
        ],
        "additional_context": "optional string"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'investor_id' not in data or 'investee_id' not in data:
            return jsonify({
                'error': 'Missing required fields: investor_id and investee_id'
            }), 400
        
        investor_id = data['investor_id']
        investee_id = data['investee_id']
        documents = data.get('documents', [])
        additional_context = data.get('additional_context', '')
        
        logger.info(f"Processing SOW generation for Investor: {investor_id}, Investee: {investee_id}")
        
        # Process documents - only extract text, don't generate SOW yet
        consolidated_text = ""
        for doc in documents:
            doc_path = doc.get('path')
            doc_type = doc.get('type', 'pdf')
            
            if doc_type == 'pdf' and doc_path and os.path.exists(doc_path):
                # Extract text from PDF (don't generate SOW yet)
                try:
                    # Use OCR handler to extract text only
                    extracted_text, used_ocr = sow_pipeline.ocr_handler.extract_text_from_pdf(doc_path)
                    if extracted_text:
                        extraction_method = "OCR" if used_ocr else "PyPDF2"
                        consolidated_text += f"\n\n--- Document: {doc.get('name', 'Unknown')} ---\n"
                        consolidated_text += f"--- Extraction Method: {extraction_method} ---\n"
                        consolidated_text += extracted_text
                        logger.info(f"Extracted {len(extracted_text)} characters from {doc.get('name')} using {extraction_method}")
                except Exception as e:
                    logger.error(f"Failed to extract text from {doc_path}: {e}")
                    # Try alternative extraction method
                    try:
                        result = sow_pipeline.ocr_handler.extract_with_fallback(doc_path)
                        if result['status'] == 'success' and result['text']:
                            consolidated_text += f"\n\n--- Document: {doc.get('name', 'Unknown')} ---\n"
                            consolidated_text += f"--- Extraction Method: {result['method']} ---\n"
                            consolidated_text += result['text']
                    except Exception as e2:
                        logger.error(f"All extraction methods failed for {doc_path}: {e2}")
            elif doc_type == 'txt' and doc_path and os.path.exists(doc_path):
                with open(doc_path, 'r', encoding='utf-8') as f:
                    consolidated_text += f"\n\n--- Document: {doc.get('name', 'Unknown')} ---\n"
                    consolidated_text += f.read()
        
        # Generate SOW using the pipeline
        if not consolidated_text:
            consolidated_text = f"Generate due diligence scope for {investee_id} investment by {investor_id}. {additional_context}"
        
        # First extract company name from text
        company_name = investee_id  # Default to investee_id
        if consolidated_text:
            try:
                extracted_company = sow_pipeline.claude_analyzer.extract_company_name(consolidated_text[:3000])
                if extracted_company and extracted_company.lower() not in ['unknown', 'not found', 'n/a']:
                    company_name = extracted_company
            except Exception as e:
                logger.warning(f"Could not extract company name: {e}")
        
        # Analyze financial content to get requirements
        requirements = sow_pipeline.analyze_financial_content_for_requirements(
            consolidated_text,
            company_name
        )
        
        # Generate scope using the pipeline's method
        sow_content = sow_pipeline._generate_strict_dd_scope(requirements)
        
        # Save versioned output
        output_file = sow_pipeline._save_versioned_output(company_name, sow_content)
        
        return jsonify({
            'status': 'success',
            'investor_id': investor_id,
            'investee_id': investee_id,
            'company_name': company_name,
            'sow_text': sow_content,
            'output_file': output_file,
            'financial_periods': requirements.get('financial_periods', 'historical period'),
            'industry': requirements.get('industry_specific', 'general'),
            'risk_areas': requirements.get('risk_areas', []),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error generating SOW: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'error': f'Failed to generate SOW: {str(e)}'
        }), 500

@app.route('/sow/to_excel', methods=['POST'])
def convert_sow_to_excel():
    """
    Convert SOW text to Excel format
    
    Expected JSON payload:
    {
        "investor_id": "string",
        "investee_id": "string",
        "sow_text": "string (SOW content)",
        "sow_file_path": "optional path to SOW file"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'investor_id' not in data or 'investee_id' not in data:
            return jsonify({
                'error': 'Missing required fields: investor_id and investee_id'
            }), 400
        
        investor_id = data['investor_id']
        investee_id = data['investee_id']
        sow_text = data.get('sow_text', '')
        sow_file_path = data.get('sow_file_path')
        
        # If no SOW text provided, try to read from file
        if not sow_text and sow_file_path and os.path.exists(sow_file_path):
            with open(sow_file_path, 'r', encoding='utf-8') as f:
                sow_text = f.read()
        
        if not sow_text:
            return jsonify({
                'error': 'No SOW text provided or found'
            }), 400
        
        logger.info(f"Converting SOW to Excel for Investor: {investor_id}, Investee: {investee_id}")
        
        # Create temporary SOW file if needed
        temp_sow_file = None
        if not sow_file_path:
            temp_sow_file = f"temp_sow_{investee_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(temp_sow_file, 'w', encoding='utf-8') as f:
                f.write(sow_text)
            sow_file_path = temp_sow_file
        
        try:
            # Process SOW to IRL using the complete pipeline
            result = irl_pipeline.process_sow_to_irl(sow_file_path)
            
            if result['status'] == 'success':
                excel_file = result.get('irl_excel_file')
            else:
                raise Exception(f"IRL generation failed: {result.get('error', 'Unknown error')}")
        finally:
            # Clean up temp file if created
            if temp_sow_file and os.path.exists(temp_sow_file):
                os.remove(temp_sow_file)
        
        if excel_file and os.path.exists(excel_file):
            return send_file(
                excel_file,
                as_attachment=True,
                download_name=f"{investee_id}_IRL_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            return jsonify({
                'error': 'Failed to create Excel file'
            }), 500
            
    except Exception as e:
        logger.error(f"Error converting SOW to Excel: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'error': f'Failed to convert SOW to Excel: {str(e)}'
        }), 500

@app.route('/irl/validate', methods=['POST'])
def validate_irl():
    """
    Validate Excel files against IRL requirements
    
    Expected form-data or JSON payload:
    {
        "investor_id": "string",
        "investee_id": "string",
        "irl_file": "file upload or path",
        "excel_files": ["file uploads or paths"],
        "validation_rules": {optional custom rules}
    }
    """
    try:
        # Handle both form-data and JSON
        if request.content_type and 'multipart/form-data' in request.content_type:
            investor_id = request.form.get('investor_id')
            investee_id = request.form.get('investee_id')
            irl_file = request.files.get('irl_file')
            excel_files = request.files.getlist('excel_files')
            validation_rules = json.loads(request.form.get('validation_rules', '{}'))
        else:
            data = request.get_json()
            investor_id = data.get('investor_id')
            investee_id = data.get('investee_id')
            irl_file = data.get('irl_file')
            excel_files = data.get('excel_files', [])
            validation_rules = data.get('validation_rules', {})
        
        # Validate required fields
        if not investor_id or not investee_id:
            return jsonify({
                'error': 'Missing required fields: investor_id and investee_id'
            }), 400
        
        logger.info(f"Validating IRL for Investor: {investor_id}, Investee: {investee_id}")
        
        # Save uploaded files temporarily
        temp_dir = Path('temp_validation') / f"{investor_id}_{investee_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        validation_results = []
        
        try:
            # Process IRL file
            irl_requirements = {}
            if irl_file:
                if hasattr(irl_file, 'save'):
                    irl_path = temp_dir / 'irl.xlsx'
                    irl_file.save(str(irl_path))
                else:
                    irl_path = Path(irl_file)
                
                # Parse IRL requirements
                irl_df = pd.read_excel(irl_path)
                # Extract requirements from IRL Excel
                irl_requirements = {
                    'investor_id': investor_id,
                    'investee_id': investee_id,
                    'requirements': []
                }
                
                # Parse IRL Excel structure
                for idx, row in irl_df.iterrows():
                    if pd.notna(row.get('Information Requirement', row.get('Info Requirement', ''))):
                        irl_requirements['requirements'].append({
                            'id': row.get('S.No.', idx),
                            'section': row.get('Section', ''),
                            'requirement': row.get('Information Requirement', row.get('Info Requirement', '')),
                            'priority': row.get('Priority', 'Medium')
                        })
            
            # Process each Excel file
            for excel_file in excel_files:
                if hasattr(excel_file, 'save'):
                    file_path = temp_dir / excel_file.filename
                    excel_file.save(str(file_path))
                    file_name = excel_file.filename
                else:
                    file_path = Path(excel_file)
                    file_name = file_path.name
                
                # Validate using the pipeline
                validation_result = validator_pipeline.process_file(str(file_path))
                
                # Add IRL requirements to the result if available
                if irl_requirements and irl_requirements.get('requirements'):
                    validation_result['irl_requirements'] = irl_requirements
                    # You could also perform custom validation against IRL requirements here
                    validation_result['irl_coverage'] = {
                        'total_requirements': len(irl_requirements.get('requirements', [])),
                        'validation_note': 'IRL requirements attached for reference'
                    }
                
                validation_results.append({
                    'file': file_name,
                    'validation': validation_result
                })
            
            # Generate summary report
            summary = {
                'total_files': len(validation_results),
                'successful': sum(1 for r in validation_results if r.get('validation', {}).get('status') == 'success'),
                'failed': sum(1 for r in validation_results if r.get('validation', {}).get('status') == 'error'),
                'validation_timestamp': datetime.now().isoformat()
            }
            
            # Save results
            output_dir = Path('validation_output') / f"{investor_id}_{investee_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save validation report
            report_file = output_dir / 'validation_report.json'
            with open(report_file, 'w') as f:
                json.dump({
                    'investor_id': investor_id,
                    'investee_id': investee_id,
                    'timestamp': datetime.now().isoformat(),
                    'results': validation_results,
                    'summary': summary
                }, f, indent=2, default=str)
            
            return jsonify({
                'status': 'success',
                'investor_id': investor_id,
                'investee_id': investee_id,
                'validation_results': validation_results,
                'summary': summary,
                'report_file': str(report_file),
                'timestamp': datetime.now().isoformat()
            })
            
        finally:
            # Cleanup temp files
            import shutil
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
                
    except Exception as e:
        logger.error(f"Error validating IRL: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'error': f'Failed to validate IRL: {str(e)}'
        }), 500

@app.route('/workflow/complete', methods=['POST'])
def complete_workflow():
    """
    Execute the complete workflow: SOW -> Excel -> Validation
    
    This endpoint chains all three APIs together for a complete process
    """
    try:
        data = request.get_json()
        
        # Step 1: Generate SOW
        logger.info("Step 1: Generating SOW...")
        sow_response = generate_sow()
        if sow_response[1] != 200:
            return sow_response
        
        sow_data = sow_response[0].get_json()
        
        # Step 2: Convert to Excel
        logger.info("Step 2: Converting SOW to Excel...")
        excel_request = {
            'investor_id': data['investor_id'],
            'investee_id': data['investee_id'],
            'sow_text': sow_data['sow_text']
        }
        
        # Mock the request context for internal call
        with app.test_request_context(json=excel_request):
            excel_response = convert_sow_to_excel()
        
        # Step 3: Validate if validation files provided
        validation_result = None
        if 'validation_files' in data:
            logger.info("Step 3: Validating against IRL...")
            validation_request = {
                'investor_id': data['investor_id'],
                'investee_id': data['investee_id'],
                'excel_files': data['validation_files']
            }
            
            with app.test_request_context(json=validation_request):
                validation_response = validate_irl()
                if validation_response[1] == 200:
                    validation_result = validation_response[0].get_json()
        
        return jsonify({
            'status': 'success',
            'workflow': 'complete',
            'sow_generation': sow_data,
            'excel_conversion': 'completed',
            'validation': validation_result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in complete workflow: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'error': f'Failed to complete workflow: {str(e)}'
        }), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Initialize pipelines on startup
    if initialize_pipelines():
        # Run the Flask app
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True
        )
    else:
        logger.error("Failed to initialize pipelines. Exiting.")
        sys.exit(1)