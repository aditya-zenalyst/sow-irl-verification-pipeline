#!/usr/bin/env python3
"""
Test if the API can start and initialize without errors
"""

import sys
import os

# Add paths to sys.path like the main API does
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'SOW'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'IRL'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Validator'))

def test_imports():
    """Test if all modules can be imported"""
    print("Testing imports...")
    
    try:
        from SOW.dynamic_dd_pipeline import DynamicDueDiligencePipeline
        print("✅ SOW.dynamic_dd_pipeline imported successfully")
    except Exception as e:
        print(f"❌ Failed to import SOW.dynamic_dd_pipeline: {e}")
        return False
    
    try:
        from IRL.irl_dd_pipeline import IRLDueDiligencePipeline
        print("✅ IRL.irl_dd_pipeline imported successfully")
    except Exception as e:
        print(f"❌ Failed to import IRL.irl_dd_pipeline: {e}")
        return False
    
    try:
        from Validator.pipeline import ExcelValidationPipeline
        from Validator.config import PipelineConfig
        print("✅ Validator modules imported successfully")
    except Exception as e:
        print(f"❌ Failed to import Validator modules: {e}")
        return False
    
    return True

def test_pipeline_initialization():
    """Test if pipelines can be initialized"""
    print("\nTesting pipeline initialization...")
    
    try:
        from SOW.dynamic_dd_pipeline import DynamicDueDiligencePipeline
        sow_pipeline = DynamicDueDiligencePipeline()
        print("✅ SOW pipeline initialized")
        
        # Test if methods exist
        assert hasattr(sow_pipeline, 'ocr_handler'), "Missing ocr_handler"
        assert hasattr(sow_pipeline.ocr_handler, 'extract_text_from_pdf'), "Missing extract_text_from_pdf method"
        assert hasattr(sow_pipeline, 'process_pdf'), "Missing process_pdf method"
        assert hasattr(sow_pipeline, '_generate_strict_dd_scope'), "Missing _generate_strict_dd_scope method"
        assert hasattr(sow_pipeline, 'analyze_financial_content_for_requirements'), "Missing analyze_financial_content_for_requirements"
        print("✅ SOW pipeline methods verified")
        
    except Exception as e:
        print(f"❌ Failed to initialize SOW pipeline: {e}")
        return False
    
    try:
        from IRL.irl_dd_pipeline import IRLDueDiligencePipeline
        irl_pipeline = IRLDueDiligencePipeline()
        print("✅ IRL pipeline initialized")
        
        # Test if methods exist
        assert hasattr(irl_pipeline, 'process_sow_to_irl'), "Missing process_sow_to_irl method"
        print("✅ IRL pipeline methods verified")
        
    except Exception as e:
        print(f"❌ Failed to initialize IRL pipeline: {e}")
        return False
    
    try:
        from Validator.pipeline import ExcelValidationPipeline
        from Validator.config import PipelineConfig
        config = PipelineConfig()
        validator_pipeline = ExcelValidationPipeline(config)
        print("✅ Validator pipeline initialized")
        
        # Test if methods exist
        assert hasattr(validator_pipeline, 'process_file'), "Missing process_file method"
        print("✅ Validator pipeline methods verified")
        
    except Exception as e:
        print(f"❌ Failed to initialize Validator pipeline: {e}")
        return False
    
    return True

def test_api_routes():
    """Test if Flask app can be created with routes"""
    print("\nTesting Flask app creation...")
    
    try:
        # Import the Flask app
        from api_main import app, initialize_pipelines
        
        # Initialize pipelines
        if initialize_pipelines():
            print("✅ Pipelines initialized via API")
        else:
            print("❌ Failed to initialize pipelines via API")
            return False
        
        # Check routes
        routes = [str(rule) for rule in app.url_map.iter_rules()]
        expected_routes = [
            '/health',
            '/sow/generate',
            '/sow/to_excel',
            '/irl/validate',
            '/workflow/complete'
        ]
        
        for route in expected_routes:
            if any(route in r for r in routes):
                print(f"✅ Route {route} registered")
            else:
                print(f"❌ Route {route} not found")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create Flask app: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all startup tests"""
    print("=" * 60)
    print("ZENALYST API STARTUP TEST")
    print("=" * 60)
    
    # Test 1: Imports
    if not test_imports():
        print("\n❌ Import test failed")
        sys.exit(1)
    
    # Test 2: Pipeline initialization
    if not test_pipeline_initialization():
        print("\n❌ Pipeline initialization test failed")
        sys.exit(1)
    
    # Test 3: API routes
    if not test_api_routes():
        print("\n❌ API routes test failed")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ ALL STARTUP TESTS PASSED")
    print("API is ready to run!")
    print("\nTo start the API, run:")
    print("   python api_main.py")
    print("=" * 60)

if __name__ == "__main__":
    main()