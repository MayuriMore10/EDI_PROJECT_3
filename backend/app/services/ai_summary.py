from typing import Dict, List, Any, Tuple
from .compare import FieldComparisonResult, FieldLengthError
from .spec_parser import EDI_810_FIELDS
import re


class ComplianceAnalyzer:
    """AI-powered compliance and validation analyzer for EDI documents."""
    
    def __init__(self):
        # Critical fields that are absolutely essential for EDI 810 processing
        self.critical_fields = {
            "ST01": "Transaction Set Identifier (must be 810)",
            "ST02": "Transaction Set Control Number",
            "BIG01": "Invoice Date",
            "BIG02": "Invoice Number", 
            "SE01": "Number of Included Segments",
            "SE02": "Transaction Set Control Number",
            "CTT01": "Number of Line Items",
            "TDS01": "Total Invoice Amount"
        }
        
        # Important fields that significantly impact processing
        self.important_fields = {
            "N101": "Entity Identifier Code",
            "N102": "Name",
            "N301": "Address Information",
            "N401": "City Name",
            "N402": "State or Province Code",
            "N403": "Postal Code",
            "IT102": "Quantity Invoiced",
            "IT103": "Unit or Basis for Measurement Code",
            "IT104": "Unit Price",
            "ITD01": "Terms Type Code",
            "ITD03": "Terms Discount Percent",
            "ITD07": "Terms Net Days",
            "REF01": "Reference Identification Qualifier",
            "REF02": "Reference Identification"
        }
        
        # Control and structural fields
        self.control_fields = {
            "ISA01": "Authorization Information Qualifier",
            "ISA06": "Interchange Sender ID",
            "ISA08": "Interchange Receiver ID",
            "ISA09": "Interchange Date",
            "ISA13": "Interchange Control Number",
            "GS01": "Functional Identifier Code",
            "GS02": "Application Sender's Code",
            "GS03": "Application Receiver's Code",
            "GS04": "Date",
            "GS06": "Group Control Number",
            "GE01": "Number of Transaction Sets Included",
            "GE02": "Group Control Number",
            "IEA01": "Number of Included Functional Groups",
            "IEA02": "Interchange Control Number"
        }
        
        self.business_rules = {
            "invoice_integrity": ["ST01", "ST02", "BIG01", "BIG02", "TDS01", "SE01", "SE02"],
            "party_identification": ["N101", "N102", "N301", "N401", "N402", "N403"],
            "item_details": ["IT102", "IT103", "IT104", "CTT01"],
            "financial_totals": ["TDS01", "CTT01"],
            "payment_terms": ["ITD01", "ITD03", "ITD07"],
            "control_structure": ["ISA13", "GS06", "ST02", "SE02"],
            "reference_data": ["REF01", "REF02", "BIG03", "BIG04"]
        }
    
    def generate_comprehensive_summary(self, 
                                     comparison_result: FieldComparisonResult,
                                     edi_fields: List[str],
                                     spec_requirements: Dict[str, bool],
                                     edi_field_values: Dict[str, str] = None) -> Dict[str, Any]:
        """Generate a comprehensive AI-powered summary of document comparison."""
        
        summary = {
            "overall_compliance": self._calculate_compliance_score(comparison_result, spec_requirements),
            "critical_issues": self._identify_critical_issues(comparison_result, edi_field_values),
            "business_impact": self._assess_business_impact(comparison_result),
            "recommendations": self._generate_recommendations(comparison_result, edi_field_values),
            "field_analysis": self._analyze_field_patterns(edi_fields, edi_field_values),
            "validation_summary": self._create_validation_summary(comparison_result),
            "compliance_categories": self._categorize_compliance(comparison_result)
        }
        
        return summary
    
    def _calculate_compliance_score(self, result: FieldComparisonResult, requirements: Dict[str, bool]) -> Dict[str, Any]:
        """Calculate overall compliance score and breakdown."""
        total_mandatory = len([k for k, v in requirements.items() if v])
        mandatory_present = len(result.mandatory_present)
        
        compliance_score = (mandatory_present / total_mandatory * 100) if total_mandatory > 0 else 100
        
        # Deduct points for length errors
        length_error_penalty = min(len(result.length_errors) * 5, 25)  # Max 25% penalty
        final_score = max(compliance_score - length_error_penalty, 0)
        
        status = "EXCELLENT" if final_score >= 95 else \
                "GOOD" if final_score >= 85 else \
                "NEEDS_IMPROVEMENT" if final_score >= 70 else \
                "CRITICAL_ISSUES"
        
        return {
            "score": round(final_score, 1),
            "status": status,
            "mandatory_completion": f"{mandatory_present}/{total_mandatory}",
            "optional_fields_used": len(result.optional_present),
            "length_errors": len(result.length_errors)
        }
    
    def _identify_critical_issues(self, result: FieldComparisonResult, field_values: Dict[str, str] = None) -> List[Dict[str, str]]:
        """Identify critical compliance issues that need immediate attention."""
        issues = []
        
        # Check for missing critical fields
        for field in result.mandatory_missing:
            if field in self.critical_fields:
                issues.append({
                    "type": "MISSING_CRITICAL_FIELD",
                    "field": field,
                    "description": f"Missing critical field: {self.critical_fields[field]}",
                    "severity": "CRITICAL",
                    "impact": "Document will likely be rejected by trading partner"
                })
            elif field in self.important_fields:
                issues.append({
                    "type": "MISSING_IMPORTANT_FIELD",
                    "field": field,
                    "description": f"Missing important field: {self.important_fields[field]}",
                    "severity": "HIGH",
                    "impact": "May cause processing delays or issues"
                })
            elif field in self.control_fields:
                issues.append({
                    "type": "MISSING_CONTROL_FIELD",
                    "field": field,
                    "description": f"Missing control field: {self.control_fields[field]}",
                    "severity": "MEDIUM",
                    "impact": "May affect document routing or validation"
                })
        
        # Check for length validation errors on all important fields
        for error in result.length_errors:
            if error.field_id in self.critical_fields:
                issues.append({
                    "type": "CRITICAL_LENGTH_ERROR",
                    "field": error.field_id,
                    "description": f"Length error in critical field: {error}",
                    "severity": "CRITICAL",
                    "impact": "Will likely cause processing errors"
                })
            elif error.field_id in self.important_fields:
                issues.append({
                    "type": "IMPORTANT_LENGTH_ERROR",
                    "field": error.field_id,
                    "description": f"Length error in important field: {error}",
                    "severity": "HIGH",
                    "impact": "May cause processing issues"
                })
            elif error.field_id in self.control_fields:
                issues.append({
                    "type": "CONTROL_LENGTH_ERROR",
                    "field": error.field_id,
                    "description": f"Length error in control field: {error}",
                    "severity": "MEDIUM",
                    "impact": "May affect document validation"
                })
        
        # Check for business rule violations
        if field_values:
            issues.extend(self._check_business_rules(field_values))
        
        return issues
    
    def _check_business_rules(self, field_values: Dict[str, str]) -> List[Dict[str, str]]:
        """Check for business rule violations."""
        issues = []
        
        # Check if ST01 is 810
        if "ST01" in field_values and field_values["ST01"] != "810":
            issues.append({
                "type": "INVALID_TRANSACTION_TYPE",
                "field": "ST01",
                "description": f"Invalid transaction type: {field_values['ST01']}. Must be 810 for invoices.",
                "severity": "CRITICAL",
                "impact": "Document will be rejected"
            })
        
        # Check date formats
        date_fields = ["BIG01", "GS04", "ISA09"]
        for field in date_fields:
            if field in field_values:
                if not self._validate_date_format(field_values[field], field):
                    issues.append({
                        "type": "INVALID_DATE_FORMAT",
                        "field": field,
                        "description": f"Invalid date format in {field}: {field_values[field]}",
                        "severity": "MEDIUM",
                        "impact": "May cause processing delays"
                    })
        
        return issues
    
    def _validate_date_format(self, date_value: str, field_type: str) -> bool:
        """Validate date formats based on field type."""
        if field_type in ["BIG01", "GS04"]:  # CCYYMMDD format
            return bool(re.match(r'^\d{8}$', date_value))
        elif field_type == "ISA09":  # YYMMDD format
            return bool(re.match(r'^\d{6}$', date_value))
        return True
    
    def _assess_business_impact(self, result: FieldComparisonResult) -> Dict[str, Any]:
        """Assess the business impact of compliance issues."""
        impact_score = 0
        impact_factors = []
        
        # Missing mandatory fields impact
        if result.mandatory_missing:
            impact_score += len(result.mandatory_missing) * 10
            impact_factors.append(f"{len(result.mandatory_missing)} mandatory fields missing")
        
        # Length errors impact
        if result.length_errors:
            impact_score += len(result.length_errors) * 5
            impact_factors.append(f"{len(result.length_errors)} field length violations")
        
        # Determine risk level
        risk_level = "LOW" if impact_score < 20 else \
                    "MEDIUM" if impact_score < 50 else \
                    "HIGH" if impact_score < 100 else "CRITICAL"
        
        return {
            "risk_level": risk_level,
            "impact_score": impact_score,
            "factors": impact_factors,
            "processing_likelihood": self._estimate_processing_success(impact_score)
        }
    
    def _estimate_processing_success(self, impact_score: int) -> str:
        """Estimate likelihood of successful processing by trading partner."""
        if impact_score < 10:
            return "Very High (>95%)"
        elif impact_score < 30:
            return "High (85-95%)"
        elif impact_score < 60:
            return "Medium (70-85%)"
        elif impact_score < 100:
            return "Low (50-70%)"
        else:
            return "Very Low (<50%)"
    
    def _generate_recommendations(self, result: FieldComparisonResult, field_values: Dict[str, str] = None) -> List[Dict[str, str]]:
        """Generate actionable recommendations for improving compliance."""
        recommendations = []
        
        # Recommendations for missing mandatory fields
        if result.mandatory_missing:
            critical_missing = [f for f in result.mandatory_missing if f in self.critical_fields]
            if critical_missing:
                recommendations.append({
                    "priority": "HIGH",
                    "category": "MISSING_FIELDS",
                    "title": "Add Critical Missing Fields",
                    "description": f"Add these critical fields: {', '.join(critical_missing)}",
                    "action": "Review your EDI mapping and ensure all mandatory fields are populated"
                })
        
        # Recommendations for length errors
        if result.length_errors:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "DATA_VALIDATION",
                "title": "Fix Field Length Issues",
                "description": f"Correct length violations in {len(result.length_errors)} fields",
                "action": "Review field specifications and adjust data to meet length requirements"
            })
        
        # Recommendations for optimization
        if len(result.optional_present) < 5:
            recommendations.append({
                "priority": "LOW",
                "category": "OPTIMIZATION",
                "title": "Consider Adding Optional Fields",
                "description": "Adding relevant optional fields can improve data richness",
                "action": "Review optional fields that might benefit your trading partners"
            })
        
        return recommendations
    
    def _analyze_field_patterns(self, edi_fields: List[str], field_values: Dict[str, str] = None) -> Dict[str, Any]:
        """Analyze patterns in field usage and data."""
        analysis = {
            "segment_distribution": self._analyze_segment_distribution(edi_fields),
            "data_quality_indicators": self._assess_data_quality(field_values) if field_values else {},
            "completeness_by_category": self._analyze_completeness_by_category(edi_fields)
        }
        
        return analysis
    
    def _analyze_segment_distribution(self, edi_fields: List[str]) -> Dict[str, int]:
        """Analyze distribution of fields across EDI segments."""
        segments = {}
        for field in edi_fields:
            segment = re.match(r'^([A-Z]+)', field)
            if segment:
                seg_name = segment.group(1)
                segments[seg_name] = segments.get(seg_name, 0) + 1
        
        return segments
    
    def _assess_data_quality(self, field_values: Dict[str, str]) -> Dict[str, Any]:
        """Assess data quality indicators."""
        if not field_values:
            return {}
        
        total_fields = len(field_values)
        empty_fields = sum(1 for v in field_values.values() if not v or v.strip() == "")
        
        return {
            "completeness_rate": round((total_fields - empty_fields) / total_fields * 100, 1),
            "empty_fields": empty_fields,
            "average_field_length": round(sum(len(v) for v in field_values.values()) / total_fields, 1),
            "data_density": "High" if empty_fields < total_fields * 0.1 else "Medium" if empty_fields < total_fields * 0.3 else "Low"
        }
    
    def _analyze_completeness_by_category(self, edi_fields: List[str]) -> Dict[str, Dict[str, int]]:
        """Analyze field completeness by business category."""
        categories = {}
        
        for category, fields in self.business_rules.items():
            present = sum(1 for field in fields if field in edi_fields)
            total = len(fields)
            categories[category] = {
                "present": present,
                "total": total,
                "percentage": round(present / total * 100, 1) if total > 0 else 0
            }
        
        return categories
    
    def _create_validation_summary(self, result: FieldComparisonResult) -> Dict[str, Any]:
        """Create a concise validation summary."""
        return {
            "total_fields_validated": len(result.mandatory_present) + len(result.mandatory_missing) + 
                                    len(result.optional_present) + len(result.optional_missing),
            "mandatory_fields": {
                "present": len(result.mandatory_present),
                "missing": len(result.mandatory_missing)
            },
            "optional_fields": {
                "present": len(result.optional_present),
                "missing": len(result.optional_missing)
            },
            "validation_errors": len(result.length_errors),
            "additional_fields": len(result.additional_fields)
        }
    
    def _categorize_compliance(self, result: FieldComparisonResult) -> Dict[str, List[str]]:
        """Categorize fields by compliance status."""
        return {
            "fully_compliant": result.mandatory_present,
            "non_compliant": result.mandatory_missing,
            "enhanced_data": result.optional_present,
            "validation_issues": [error.field_id for error in result.length_errors],
            "additional_data": result.additional_fields
        }


def generate_executive_summary(analysis: Dict[str, Any]) -> str:
    """Generate a human-readable executive summary."""
    compliance = analysis["overall_compliance"]
    impact = analysis["business_impact"]
    
    summary_parts = [
        f"📊 **Compliance Score: {compliance['score']}% ({compliance['status']})**",
        f"🎯 **Mandatory Fields: {compliance['mandatory_completion']} completed**",
        f"⚠️ **Risk Level: {impact['risk_level']}**",
        f"📈 **Processing Success Likelihood: {impact['processing_likelihood']}**"
    ]
    
    if analysis["critical_issues"]:
        summary_parts.append(f"🚨 **Critical Issues: {len(analysis['critical_issues'])} found**")
    
    if analysis["recommendations"]:
        high_priority = len([r for r in analysis["recommendations"] if r["priority"] == "HIGH"])
        if high_priority > 0:
            summary_parts.append(f"🔧 **High Priority Actions: {high_priority} recommended**")
    
    return "\n".join(summary_parts)
