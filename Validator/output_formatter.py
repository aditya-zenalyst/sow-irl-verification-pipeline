"""
Output formatter for generating reports from validation results
"""

import json
import csv
from pathlib import Path
from typing import Dict, Any, List
import logging
from datetime import datetime


class OutputFormatter:
    """Format validation results for output"""
    
    def __init__(self, config: Any):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def generate_report(self, results: List[Dict], summary: Dict) -> str:
        """Generate HTML report from results"""
        html_template = """<!DOCTYPE html>
<html>
<head>
    <title>Excel Validation Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        h1, h2, h3 {{
            color: #333;
        }}
        .summary {{
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .file-result {{
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .success {{
            color: green;
            font-weight: bold;
        }}
        .error {{
            color: red;
            font-weight: bold;
        }}
        .pending {{
            color: orange;
            font-weight: bold;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        th, td {{
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f8f8f8;
            font-weight: bold;
        }}
        .metadata {{
            background-color: #f8f8f8;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
        }}
        .sheet-info {{
            margin-left: 20px;
            margin-top: 10px;
            padding: 10px;
            background-color: #fafafa;
            border-left: 3px solid #4CAF50;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .stat-card {{
            background-color: #f8f8f8;
            padding: 15px;
            border-radius: 4px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }}
        .stat-label {{
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <h1>Excel Validation Report</h1>
    <p>Generated: {timestamp}</p>
    
    <div class="summary">
        <h2>Summary</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{total_files}</div>
                <div class="stat-label">Total Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: green;">{successful}</div>
                <div class="stat-label">Successful</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: red;">{failed}</div>
                <div class="stat-label">Failed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sheets_processed}</div>
                <div class="stat-label">Sheets Processed</div>
            </div>
        </div>
        
        <h3>Structure Types Found</h3>
        <table>
            <tr>
                <th>Type</th>
                <th>Count</th>
            </tr>
            {structure_types_rows}
        </table>
    </div>
    
    <h2>File Results</h2>
    {file_results}
    
</body>
</html>"""
        
        # Format structure types
        structure_types_rows = ""
        for struct_type, count in summary.get("structure_types", {}).items():
            structure_types_rows += f"<tr><td>{struct_type}</td><td>{count}</td></tr>"
            
        # Format file results
        file_results_html = ""
        for result in results:
            status_class = result.get("status", "pending")
            file_results_html += self.format_file_result(result)
            
        # Fill template
        html = html_template.format(
            timestamp=summary.get("timestamp", datetime.now().isoformat()),
            total_files=summary.get("total_files", 0),
            successful=summary.get("successful", 0),
            failed=summary.get("failed", 0),
            sheets_processed=summary.get("sheets_processed", 0),
            structure_types_rows=structure_types_rows,
            file_results=file_results_html
        )
        
        return html
    
    def format_file_result(self, result: Dict) -> str:
        """Format a single file result"""
        status_class = result.get("status", "pending")
        file_name = result.get("file_name", "Unknown")
        
        html = f"""
        <div class="file-result">
            <h3>{file_name} - <span class="{status_class}">{status_class.upper()}</span></h3>
        """
        
        # Add metadata
        if result.get("metadata"):
            html += """
            <div class="metadata">
                <h4>File Metadata</h4>
                <pre>{}</pre>
            </div>
            """.format(json.dumps(result["metadata"], indent=2))
            
        # Add sheets information
        for sheet_name, sheet_data in result.get("sheets", {}).items():
            html += self.format_sheet_result(sheet_name, sheet_data)
            
        # Add errors if any
        if result.get("errors"):
            html += """
            <div class="error">
                <h4>Errors</h4>
                <ul>
            """
            for error in result["errors"]:
                html += f"<li>{error.get('type', 'Unknown')}: {error.get('message', '')}</li>"
            html += "</ul></div>"
            
        html += "</div>"
        return html
    
    def format_sheet_result(self, sheet_name: str, sheet_data: Dict) -> str:
        """Format a single sheet result"""
        structure_type = sheet_data.get("structure_type", "unknown")
        
        html = f"""
        <div class="sheet-info">
            <h4>Sheet: {sheet_name}</h4>
            <p><strong>Structure Type:</strong> {structure_type}</p>
        """
        
        # Add cleaned data preview for structured data
        if sheet_data.get("cleaned_data") and structure_type == "structured":
            cleaned = sheet_data["cleaned_data"]
            if cleaned.get("metadata"):
                html += "<h5>Column Information</h5><table>"
                html += "<tr><th>Column</th><th>Type</th><th>Missing</th><th>Description</th></tr>"
                
                columns = cleaned["metadata"].get("columns", [])
                data_types = cleaned["metadata"].get("data_types", {})
                missing_values = cleaned["metadata"].get("missing_values", {})
                descriptions = cleaned["metadata"].get("column_descriptions", {})
                
                for col in columns:
                    dtype = data_types.get(col, "unknown")
                    missing = missing_values.get(col, {}).get("percentage", 0)
                    desc = self.format_column_description(descriptions.get(col, {}))
                    
                    html += f"""
                    <tr>
                        <td>{col}</td>
                        <td>{dtype}</td>
                        <td>{missing}%</td>
                        <td>{desc}</td>
                    </tr>
                    """
                    
                html += "</table>"
                
                # Add data preview
                if cleaned.get("data"):
                    html += f"<p><strong>Data Preview</strong> (showing first 5 rows of {cleaned['metadata'].get('row_count', 0)} total)</p>"
                    html += "<table>"
                    
                    # Headers
                    html += "<tr>"
                    for col in columns[:10]:  # Limit to 10 columns for display
                        html += f"<th>{col}</th>"
                    html += "</tr>"
                    
                    # Data rows
                    for row in cleaned["data"][:5]:
                        html += "<tr>"
                        for val in row[:10]:
                            html += f"<td>{val if val is not None else ''}</td>"
                        html += "</tr>"
                        
                    html += "</table>"
                    
        # Add unstructured data preview
        elif sheet_data.get("cleaned_data") and structure_type == "unstructured":
            cleaned = sheet_data["cleaned_data"]
            if cleaned.get("content"):
                html += "<h5>Extracted Content</h5>"
                html += "<pre>{}</pre>".format(
                    json.dumps(cleaned["content"], indent=2)[:1000] + "..."
                    if len(json.dumps(cleaned["content"])) > 1000
                    else json.dumps(cleaned["content"], indent=2)
                )
                
        # Add errors if any
        if sheet_data.get("errors"):
            html += "<div class='error'><h5>Sheet Errors</h5><ul>"
            for error in sheet_data["errors"]:
                html += f"<li>{error.get('message', '')}</li>"
            html += "</ul></div>"
            
        html += "</div>"
        return html
    
    def format_column_description(self, desc: Dict) -> str:
        """Format column description for display"""
        if not desc:
            return ""
            
        parts = []
        
        if "unique_count" in desc:
            parts.append(f"{desc['unique_count']} unique")
            
        if "min" in desc and "max" in desc:
            parts.append(f"range: {desc['min']:.2f} - {desc['max']:.2f}")
            
        if "top_values" in desc:
            top = list(desc["top_values"].keys())[:3]
            parts.append(f"top: {', '.join(map(str, top))}")
            
        if "min_length" in desc and "max_length" in desc:
            parts.append(f"length: {desc['min_length']}-{desc['max_length']}")
            
        return "; ".join(parts)
    
    def export_to_json(self, results: List[Dict], output_path: Path):
        """Export results to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
            
    def export_to_csv(self, results: List[Dict], output_path: Path):
        """Export summary to CSV file"""
        rows = []
        
        for result in results:
            base_row = {
                "file_name": result.get("file_name"),
                "file_path": result.get("file_path"),
                "status": result.get("status"),
                "sheets_count": len(result.get("sheets", {}))
            }
            
            for sheet_name, sheet_data in result.get("sheets", {}).items():
                row = base_row.copy()
                row.update({
                    "sheet_name": sheet_name,
                    "structure_type": sheet_data.get("structure_type"),
                    "errors": len(sheet_data.get("errors", []))
                })
                
                if sheet_data.get("cleaned_data"):
                    cleaned = sheet_data["cleaned_data"]
                    if cleaned.get("metadata"):
                        meta = cleaned["metadata"]
                        row.update({
                            "row_count": meta.get("row_count"),
                            "column_count": meta.get("column_count"),
                            "columns": ", ".join(meta.get("columns", []))
                        })
                        
                rows.append(row)
                
        if rows:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)