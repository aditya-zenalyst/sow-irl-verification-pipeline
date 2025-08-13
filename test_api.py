#!/usr/bin/env python3
"""
Test script for the unified API to verify all endpoints work correctly
"""

import requests
import json
import os
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:5000"

def test_health_check():
    """Test the health check endpoint"""
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        return True
    return False

def test_sow_generation():
    """Test SOW generation endpoint"""
    print("\n=== Testing SOW Generation ===")
    
    # Test without documents (just context)
    payload = {
        "investor_id": "INV001",
        "investee_id": "ABC_Corporation",
        "additional_context": "Technology company focused on SaaS products, seeking Series B funding"
    }
    
    print("Testing without documents...")
    response = requests.post(
        f"{BASE_URL}/sow/generate",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Success! Company: {data.get('company_name', 'N/A')}")
        print(f"Output file: {data.get('output_file', 'N/A')}")
        print(f"SOW Text Length: {len(data.get('sow_text', ''))}")
        return data
    else:
        print(f"Error: {response.text}")
        return None

def test_sow_with_document():
    """Test SOW generation with a document"""
    print("\n=== Testing SOW Generation with Document ===")
    
    # Create a test text document
    test_doc_path = "test_financial_doc.txt"
    with open(test_doc_path, 'w') as f:
        f.write("""
        XYZ Technologies Ltd.
        Financial Statement Summary
        
        Revenue: $10M (2023)
        EBITDA: $2M (2023)
        
        The company operates in the software industry with primary focus on
        cloud-based solutions for enterprise clients.
        """)
    
    payload = {
        "investor_id": "INV002",
        "investee_id": "XYZ_Tech",
        "documents": [
            {
                "name": "Financial Summary",
                "type": "txt",
                "path": test_doc_path
            }
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/sow/generate",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Success! Company: {data.get('company_name', 'N/A')}")
        print(f"Industry: {data.get('industry', 'N/A')}")
        print(f"Financial Periods: {data.get('financial_periods', 'N/A')}")
        
        # Clean up test file
        os.remove(test_doc_path)
        return data
    else:
        print(f"Error: {response.text}")
        # Clean up test file
        if os.path.exists(test_doc_path):
            os.remove(test_doc_path)
        return None

def test_sow_to_excel(sow_data):
    """Test SOW to Excel conversion"""
    print("\n=== Testing SOW to Excel Conversion ===")
    
    if not sow_data:
        print("No SOW data available for testing")
        return None
    
    payload = {
        "investor_id": sow_data.get('investor_id'),
        "investee_id": sow_data.get('investee_id'),
        "sow_text": sow_data.get('sow_text')
    }
    
    response = requests.post(
        f"{BASE_URL}/sow/to_excel",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        # Save the Excel file
        output_file = f"{sow_data.get('investee_id', 'test')}_IRL_test.xlsx"
        with open(output_file, 'wb') as f:
            f.write(response.content)
        print(f"Excel file saved as: {output_file}")
        return output_file
    else:
        print(f"Error: {response.text}")
        return None

def test_validation():
    """Test IRL validation endpoint"""
    print("\n=== Testing IRL Validation ===")
    
    # Create a simple test Excel file
    import pandas as pd
    test_excel = "test_validation.xlsx"
    df = pd.DataFrame({
        'Company': ['Test Corp'],
        'Revenue': [1000000],
        'Expenses': [800000],
        'Profit': [200000]
    })
    df.to_excel(test_excel, index=False)
    
    payload = {
        "investor_id": "INV003",
        "investee_id": "TEST_CORP",
        "excel_files": [test_excel]
    }
    
    response = requests.post(
        f"{BASE_URL}/irl/validate",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Validation Summary: {json.dumps(data.get('summary', {}), indent=2)}")
        # Clean up
        os.remove(test_excel)
        return True
    else:
        print(f"Error: {response.text}")
        # Clean up
        if os.path.exists(test_excel):
            os.remove(test_excel)
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("ZENALYST API TEST SUITE")
    print("=" * 60)
    
    # Test 1: Health Check
    health_ok = test_health_check()
    if not health_ok:
        print("\n❌ API is not running. Please start the API first with:")
        print("   python api_main.py")
        return
    
    # Test 2: SOW Generation without documents
    sow_data = test_sow_generation()
    
    # Test 3: SOW Generation with documents
    sow_data_with_doc = test_sow_with_document()
    
    # Test 4: SOW to Excel conversion
    excel_file = None
    if sow_data:
        excel_file = test_sow_to_excel(sow_data)
    
    # Test 5: Validation
    test_validation()
    
    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()