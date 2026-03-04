import os
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
import yaml

class XMLBestPracticesAnalyzer:
    """Analyzes Aras Innovator Method XML files for best practices and compliance"""
    
    def __init__(self, xml_file_path):
        self.xml_file_path = xml_file_path
        self.filename = os.path.basename(xml_file_path)
        self.issues = []
        self.method_data = {}
        self.rules = self.load_rules()

    def load_rules(self):
        """Load rule definitions from YAML file located alongside this script"""
        rules_file = os.path.join(os.path.dirname(__file__), 'rules.yaml')
        try:
            with open(rules_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception:
            # If rules file cannot be loaded, return empty dict and defaults will apply
            return {}
        
    def parse_xml(self):
        """Parse XML file and extract method data"""
        try:
            tree = ET.parse(self.xml_file_path)
            root = tree.getroot()
            
            # Extract method data
            self.method_data = {
                'name': root.findtext('name', ''),
                'method_type': root.findtext('method_type', ''),
                'execution_allowed_to': root.findtext('execution_allowed_to', ''),
                'language': root.findtext('language', ''),
                'method_code': root.findtext('method_code', '')
            }
            return True
        except Exception as e:
            self.issues.append({
                'field': 'xml_parse',
                'severity': 'error',
                'message': f'Failed to parse XML: {str(e)}'
            })
            return False
    
    def check_naming_conventions(self):
        """Validate method naming conventions using rule definitions"""
        name = self.method_data.get('name', '')
        rules = self.rules.get('naming_conventions', {})

        if not name:
            self.issues.append({
                'field': 'name',
                'severity': 'error',
                'message': 'Method name is missing'
            })
            return

        # Prefix rule
        prefix_rule = rules.get('prefix', {})
        prefix_value = prefix_rule.get('value', 'HRDE')
        prefix_sev = prefix_rule.get('severity', 'warning')
        prefix_msg = prefix_rule.get('message', 'Method name does not follow prefix convention')
        if not name.startswith(prefix_value):
            self.issues.append({
                'field': 'name',
                'severity': prefix_sev,
                'message': f"{prefix_msg}: {name}"
            })

        # Indicator rule
        indicator_rule = rules.get('indicator', {})
        patterns = indicator_rule.get('patterns', [])
        indicator_sev = indicator_rule.get('severity', 'warning')
        indicator_msg = indicator_rule.get('message', 'Method name lacks required indicator')
        if patterns:
            if not any(p in name for p in patterns):
                self.issues.append({
                    'field': 'name',
                    'severity': indicator_sev,
                    'message': f"{indicator_msg}: {name}"
                })

        # Mth presence rule
        mth_rule = rules.get('mth_presence', {})
        mth_pattern = mth_rule.get('pattern', 'Mth')
        mth_sev = mth_rule.get('severity', 'warning')
        mth_msg = mth_rule.get('message', 'Method name missing "Mth" prefix')
        if mth_pattern and mth_pattern not in name:
            self.issues.append({
                'field': 'name',
                'severity': mth_sev,
                'message': f"{mth_msg}: {name}"
            })

        # PascalCase rule
        pascal_rule = rules.get('pascal_after_mth', {})
        pascal_sev = pascal_rule.get('severity', 'info')
        pascal_msg = pascal_rule.get('message', 'Ensure PascalCase after "Mth"')
        parts = name.split(mth_pattern)
        if len(parts) > 1:
            method_part = parts[1]
            if method_part and not method_part[0].isupper():
                self.issues.append({
                    'field': 'name',
                    'severity': pascal_sev,
                    'message': f"{pascal_msg}: {name}"
                })
    
    def check_configuration_completeness(self):
        """Validate required configuration fields using rule definitions"""
        config_rules = self.rules.get('configuration_completeness', {})
        # method_type
        method_type = self.method_data.get('method_type', '').strip()
        mt_rules = config_rules.get('method_type', {})
        if mt_rules.get('required', False) and not method_type:
            self.issues.append({
                'field': 'method_type',
                'severity': mt_rules.get('severity_missing', 'error'),
                'message': 'method_type is missing or empty'
            })
        elif method_type and 'valid_values' in mt_rules and method_type not in mt_rules['valid_values']:
            self.issues.append({
                'field': 'method_type',
                'severity': mt_rules.get('severity_invalid', 'warning'),
                'message': f"method_type should be one of {mt_rules.get('valid_values')}, got: {method_type}"
            })

        # execution_allowed_to
        exec_rules = config_rules.get('execution_allowed_to', {})
        execution_allowed = self.method_data.get('execution_allowed_to', '').strip()
        if exec_rules.get('required', False) and not execution_allowed:
            self.issues.append({
                'field': 'execution_allowed_to',
                'severity': exec_rules.get('severity_missing', 'error'),
                'message': 'execution_allowed_to is missing or empty (should define access rights)'
            })
        elif execution_allowed and 'valid_values' in exec_rules and execution_allowed not in exec_rules['valid_values']:
            self.issues.append({
                'field': 'execution_allowed_to',
                'severity': exec_rules.get('severity_invalid', 'warning'),
                'message': f"execution_allowed_to value \"{execution_allowed}\" may not be standard"
            })

        # language
        lang_rules = config_rules.get('language', {})
        language = self.method_data.get('language', '').strip()
        if lang_rules.get('required', False) and not language:
            self.issues.append({
                'field': 'language',
                'severity': lang_rules.get('severity_missing', 'error'),
                'message': 'language is missing or empty'
            })
        elif language and 'valid_values' in lang_rules and language not in lang_rules['valid_values']:
            self.issues.append({
                'field': 'language',
                'severity': lang_rules.get('severity_invalid', 'warning'),
                'message': f"language should be one of {lang_rules.get('valid_values')}, got: {language}"
            })

        # method_code
        code_rules = config_rules.get('method_code', {})
        method_code = self.method_data.get('method_code', '').strip()
        if code_rules.get('required', False) and not method_code:
            self.issues.append({
                'field': 'method_code',
                'severity': code_rules.get('severity_missing', 'error'),
                'message': 'method_code is missing or empty'
            })
        elif method_code and 'min_length' in code_rules and len(method_code) < code_rules['min_length']:
            self.issues.append({
                'field': 'method_code',
                'severity': code_rules.get('severity_short', 'warning'),
                'message': 'method_code appears to be too short'
            })
    
    def check_aras_best_practices(self):
        """Validate Aras-specific best practices according to rules"""
        bp_rules = self.rules.get('aras_best_practices', {})
        language = self.method_data.get('language', '')
        method_code = self.method_data.get('method_code', '')
        method_type = self.method_data.get('method_type', '')

        if not method_code:
            return

        # getInnovator rule
        gi_rule = bp_rules.get('getInnovator', {})
        if gi_rule:
            if language == gi_rule.get('language') and method_type == gi_rule.get('method_type'):
                if gi_rule.get('message') and 'getInnovator()' not in method_code:
                    self.issues.append({
                        'field': 'aras_practices',
                        'severity': gi_rule.get('severity', 'info'),
                        'message': gi_rule.get('message')
                    })
        # return statement rule
        ret_rule = bp_rules.get('return_statement', {})
        if ret_rule and ret_rule.get('message'):
            lang_list = ret_rule.get('languages')
            apply_rule = True
            if lang_list is not None:
                apply_rule = language in lang_list
            if apply_rule and 'return' not in method_code.lower():
                self.issues.append({
                    'field': 'aras_practices',
                    'severity': ret_rule.get('severity', 'warning'),
                    'message': ret_rule.get('message')
                })

        # must return item rule
        mrule = bp_rules.get('must_return_item', {})
        if mrule:
            langs = mrule.get('languages')
            apply_m = True
            if langs is not None:
                apply_m = language in langs
            if mrule.get('method_type') and mrule.get('method_type') != method_type:
                apply_m = False
            if apply_m:
                # simple heuristic: there must be a return and the final line starts with return
                lines = [l.strip() for l in method_code.splitlines() if l.strip()]
                has_return = any('return' in l for l in lines)
                ends_with_return = bool(lines and lines[-1].startswith('return'))
                if not has_return:
                    self.issues.append({
                        'field': 'aras_practices',
                        'severity': mrule.get('severity', 'error'),
                        'message': mrule.get('message') + ' (no return statement found)'
                    })
                elif not ends_with_return:
                    self.issues.append({
                        'field': 'aras_practices',
                        'severity': mrule.get('severity', 'error'),
                        'message': mrule.get('message') + ' (no unconditional return at end)'
                    })
    
    def generate_report(self):
        """Generate JSON report"""
        report = {
            'file': self.filename,
            'file_path': self.xml_file_path,
            'analysis_date': datetime.now().isoformat(),
            'method_name': self.method_data.get('name', 'Unknown'),
            'method_type': self.method_data.get('method_type', 'Unknown'),
            'language': self.method_data.get('language', 'Unknown'),
            'total_issues': len(self.issues),
            'severity_breakdown': {
                'error': len([i for i in self.issues if i['severity'] == 'error']),
                'warning': len([i for i in self.issues if i['severity'] == 'warning']),
                'info': len([i for i in self.issues if i['severity'] == 'info'])
            },
            'issues': self.issues,
            'status': 'PASS' if len([i for i in self.issues if i['severity'] == 'error']) == 0 else 'FAIL'
        }
        return report
    
    def analyze(self):
        """Run all analysis checks"""
        if not self.parse_xml():
            return self.generate_report()
        
        self.check_naming_conventions()
        self.check_configuration_completeness()
        self.check_aras_best_practices()
        
        return self.generate_report()


def analyze_all_methods(packages_path):
    """Analyze all method XML files in the packages directory"""
    results = []
    
    for root, dirs, files in os.walk(packages_path):
        for file in files:
            if file.endswith('.xml'):
                file_path = os.path.join(root, file)
                analyzer = XMLBestPracticesAnalyzer(file_path)
                report = analyzer.analyze()
                results.append(report)
    
    return results


def save_report(results, output_path):
    """Save analysis results to JSON file"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Report saved to: {output_path}")


if __name__ == "__main__":
    packages_path = r"d:\AI LLM\ARAS CODING\AML-packages"
    output_file = r"d:\AI LLM\ARAS CODING\Tools\analysis_report.json"
    
    print("Analyzing XML files...")
    results = analyze_all_methods(packages_path)
    
    print(f"Found {len(results)} method(s)")
    
    save_report(results, output_file)
    
    # Print summary
    total_errors = sum(r['severity_breakdown']['error'] for r in results)
    total_warnings = sum(r['severity_breakdown']['warning'] for r in results)
    total_info = sum(r['severity_breakdown']['info'] for r in results)
    
    print(f"\n=== Analysis Summary ===")
    print(f"Total Issues: {len([i for r in results for i in r['issues']])}")
    print(f"  Errors: {total_errors}")
    print(f"  Warnings: {total_warnings}")
    print(f"  Info: {total_info}")
    print(f"Pass Rate: {sum(1 for r in results if r['status'] == 'PASS')}/{len(results)}")
