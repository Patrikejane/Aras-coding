import os
import xml.etree.ElementTree as ET
import json
from pathlib import Path
from datetime import datetime

class MethodCodeExtractor:
    """Extracts method code from Aras Innovator Method XML files"""
    
    def __init__(self, xml_file_path, output_base_path):
        self.xml_file_path = xml_file_path
        self.output_base_path = output_base_path
        self.filename = os.path.basename(xml_file_path)
        self.extraction_log = []
        
    def parse_xml(self):
        """Parse XML file and extract relevant data"""
        try:
            tree = ET.parse(self.xml_file_path)
            root = tree.getroot()
            
            data = {
                'name': root.findtext('name', ''),
                'method_type': root.findtext('method_type', ''),
                'language': root.findtext('language', ''),
                'method_code': root.findtext('method_code', '')
            }
            return data
        except Exception as e:
            self.log_error(f'Failed to parse XML: {str(e)}')
            return None
    
    def clean_code(self, code):
        """Clean extracted code (remove CDATA markers and extra whitespace)"""
        if not code:
            return ''
        
        # Remove CDATA markers if present
        code = code.replace('<![CDATA[', '').replace(']]>', '')
        
        # Strip leading/trailing whitespace but preserve internal formatting
        code = code.strip()
        
        return code
    
    def get_extension(self, language):
        """Get file extension based on language"""
        extensions = {
            'C#': '.cs',
            'JavaScript': '.js',
            'csharp': '.cs',
            'javascript': '.js'
        }
        return extensions.get(language, '.txt')
    
    def get_language_folder(self, language):
        """Get appropriate folder for language"""
        if 'C#' in language or language.lower() == 'csharp':
            return 'cs'
        elif 'JavaScript' in language or language.lower() == 'javascript':
            return 'js'
        else:
            return 'other'
    
    def save_extracted_code(self, method_name, language, code):
        """Save extracted code to file"""
        try:
            # Determine output folder
            lang_folder = self.get_language_folder(language)
            output_dir = os.path.join(self.output_base_path, 'extracted', lang_folder)
            
            # Create directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Create output file
            extension = self.get_extension(language)
            output_file = os.path.join(output_dir, f"{method_name}{extension}")
            
            # Write code to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            self.log_success(f'Extracted to: {output_file}')
            return output_file
            
        except Exception as e:
            self.log_error(f'Failed to save code: {str(e)}')
            return None
    
    def log_success(self, message):
        """Log successful operation"""
        self.extraction_log.append({
            'status': 'success',
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        print(f"✓ {message}")
    
    def log_error(self, message):
        """Log error"""
        self.extraction_log.append({
            'status': 'error',
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        print(f"✗ {message}")
    
    def extract(self):
        """Extract method code from XML"""
        # Parse XML
        data = self.parse_xml()
        if not data:
            return None
        
        method_name = data.get('name', 'Unknown')
        language = data.get('language', '')
        code = data.get('method_code', '')
        
        if not code:
            self.log_error(f'{method_name}: No method code found')
            return None
        
        # Clean code
        cleaned_code = self.clean_code(code)
        
        # Save code
        output_file = self.save_extracted_code(method_name, language, cleaned_code)
        
        if output_file:
            return {
                'method_name': method_name,
                'method_type': data.get('method_type'),
                'language': language,
                'output_file': output_file,
                'source_file': self.xml_file_path,
                'code_length': len(cleaned_code),
                'extraction_status': 'success'
            }
        else:
            return {
                'method_name': method_name,
                'extraction_status': 'failed',
                'source_file': self.xml_file_path
            }


def extract_all_methods(packages_path, output_base_path):
    """Extract all method codes from package directory"""
    extraction_results = []
    
    for root, dirs, files in os.walk(packages_path):
        for file in files:
            if file.endswith('.xml'):
                file_path = os.path.join(root, file)
                extractor = MethodCodeExtractor(file_path, output_base_path)
                result = extractor.extract()
                
                if result:
                    extraction_results.append(result)
    
    return extraction_results


def save_extraction_manifest(results, output_path):
    """Save extraction manifest as JSON"""
    manifest = {
        'extraction_date': datetime.now().isoformat(),
        'total_methods': len(results),
        'methods': results,
        'summary': {
            'by_language': {},
            'by_status': {}
        }
    }
    
    # Build summary
    for result in results:
        language = result.get('language', 'unknown')
        status = result.get('extraction_status', 'unknown')
        
        manifest['summary']['by_language'][language] = manifest['summary']['by_language'].get(language, 0) + 1
        manifest['summary']['by_status'][status] = manifest['summary']['by_status'].get(status, 0) + 1
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    print(f"Manifest saved to: {output_path}")


if __name__ == "__main__":
    packages_path = r"d:\AI LLM\ARAS CODING\AML-packages"
    output_base_path = r"d:\AI LLM\ARAS CODING\Tools"
    manifest_file = r"d:\AI LLM\ARAS CODING\Tools\extraction_manifest.json"
    
    print("Extracting method codes...\n")
    results = extract_all_methods(packages_path, output_base_path)
    
    print(f"\n=== Extraction Summary ===")
    print(f"Total methods extracted: {len(results)}")
    
    if results:
        by_language = {}
        for result in results:
            lang = result.get('language', 'unknown')
            by_language[lang] = by_language.get(lang, 0) + 1
        
        print(f"By Language:")
        for lang, count in by_language.items():
            print(f"  {lang}: {count}")
    
    save_extraction_manifest(results, manifest_file)
