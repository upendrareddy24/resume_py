"""
Word Document (DOCX) Generator for Resumes and Cover Letters
Generates professional documents with precise formatting control
"""
import os
from typing import Optional
from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.style import WD_STYLE_TYPE
from datetime import datetime


class WordDocumentGenerator:
    """Generate professional Word documents for resumes and cover letters"""
    
    def __init__(self):
        pass
    
    def generate_resume_docx(
        self,
        content: str,
        output_path: str,
        job_title: str = "",
        company_name: str = "",
        candidate_name: str = ""
    ) -> bool:
        """
        Generate a professional 2-page resume in DOCX format
        
        Args:
            content: Resume text content
            output_path: Path to save the DOCX
            job_title: Target job title
            company_name: Target company name
            candidate_name: Candidate's name
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Create document
            doc = Document()
            
            # Set margins (1 inch all around)
            sections = doc.sections
            for section in sections:
                section.top_margin = Inches(0.75)
                section.bottom_margin = Inches(0.75)
                section.left_margin = Inches(0.75)
                section.right_margin = Inches(0.75)
            
            # Parse content into sections
            sections_dict = self._parse_resume_content(content)
            
            print(f"  [docx-debug] Found sections: {list(sections_dict.keys())}")
            
            # Extract or use provided candidate name
            name_to_display = candidate_name
            if not name_to_display and content:
                first_line = content.split('\n')[0].strip()
                if first_line and len(first_line) < 50 and not any(kw in first_line.lower() for kw in ['target', 'position', 'github', '@']):
                    name_to_display = first_line
            
            # Header: Name
            if name_to_display:
                name_para = doc.add_paragraph(name_to_display)
                name_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                name_run = name_para.runs[0]
                name_run.font.size = Pt(18)
                name_run.font.bold = True
                name_run.font.color.rgb = RGBColor(0, 0, 0)
            
            # Contact Info
            if 'contact' in sections_dict:
                contact_text = sections_dict['contact'].replace('\n', ' | ')
                contact_para = doc.add_paragraph(contact_text)
                contact_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                contact_run = contact_para.runs[0]
                contact_run.font.size = Pt(10)
                contact_run.font.color.rgb = RGBColor(80, 80, 80)
            
            # Add spacing
            doc.add_paragraph()
            
            # Target Position
            if job_title and company_name:
                target_para = doc.add_paragraph()
                target_para.add_run('Target Position: ').bold = True
                target_para.add_run(f'{job_title} at {company_name}')
                target_para.paragraph_format.space_after = Pt(12)
            
            # Professional Summary (10 bullet points)
            summary_added = False
            for key in ['summary', 'professional_summary', 'objective']:
                if key in sections_dict and sections_dict[key].strip():
                    # Section header
                    self._add_section_header(doc, "PROFESSIONAL SUMMARY")
                    
                    summary_text = sections_dict[key]
                    summary_lines = [l.strip() for l in summary_text.split('\n') if l.strip()]
                    bullet_count = 0
                    
                    for line in summary_lines:
                        # Skip section headers
                        if line.isupper() and len(line) < 50:
                            continue
                        
                        # Clean up the line
                        clean_line = line.lstrip('•-*►▪→◆ ').strip()
                        
                        if clean_line and len(clean_line) > 20:
                            self._add_bullet_point(doc, clean_line)
                            bullet_count += 1
                            if bullet_count >= 10:
                                break
                    
                    if bullet_count > 0:
                        summary_added = True
                        doc.add_paragraph()  # Spacing
                    break
            
            # Default summary if none found
            if not summary_added:
                self._add_section_header(doc, "PROFESSIONAL SUMMARY")
                self._add_bullet_point(doc, "Experienced professional with a proven track record of delivering high-quality results")
                self._add_bullet_point(doc, "Strong technical skills and ability to work in fast-paced environments")
                self._add_bullet_point(doc, "Excellent communication and collaboration abilities")
                doc.add_paragraph()
            
            # Work Experience
            experience_added = False
            for key in ['experience', 'work_experience', 'employment']:
                if key in sections_dict and sections_dict[key].strip():
                    self._add_section_header(doc, "WORK EXPERIENCE")
                    
                    exp_text = sections_dict[key]
                    experiences = self._parse_experiences(exp_text)
                    
                    if experiences:
                        for exp in experiences[:3]:  # Top 3 most recent
                            # Company and Position
                            position = exp.get('position', 'Position')
                            company = exp.get('company', 'Company')
                            
                            job_para = doc.add_paragraph()
                            job_run = job_para.add_run(f"{position} | {company}")
                            job_run.font.size = Pt(11)
                            job_run.font.bold = True
                            job_para.paragraph_format.space_before = Pt(6)
                            job_para.paragraph_format.space_after = Pt(3)
                            
                            # Date and Location
                            if exp.get('dates') or exp.get('location'):
                                date_loc = []
                                if exp.get('dates'):
                                    date_loc.append(exp['dates'])
                                if exp.get('location'):
                                    date_loc.append(exp['location'])
                                
                                date_para = doc.add_paragraph(' | '.join(date_loc))
                                date_run = date_para.runs[0]
                                date_run.font.size = Pt(10)
                                date_run.font.italic = True
                                date_run.font.color.rgb = RGBColor(100, 100, 100)
                                date_para.paragraph_format.space_after = Pt(6)
                            
                            # Bullet points
                            for bullet in exp.get('bullets', [])[:6]:
                                self._add_bullet_point(doc, bullet)
                        
                        experience_added = True
                    else:
                        # Fallback rendering
                        exp_lines = [l.strip() for l in exp_text.split('\n') if l.strip()]
                        for line in exp_lines[:20]:
                            if line.startswith('•') or line.startswith('-'):
                                self._add_bullet_point(doc, line.lstrip('•-*►▪→◆ '))
                            else:
                                para = doc.add_paragraph(line)
                                para.paragraph_format.space_after = Pt(6)
                        experience_added = True
                    
                    doc.add_paragraph()  # Spacing
                    break
            
            # Education
            for key in ['education', 'academic']:
                if key in sections_dict and sections_dict[key].strip():
                    self._add_section_header(doc, "EDUCATION")
                    
                    edu_text = sections_dict[key]
                    edu_lines = [l.strip() for l in edu_text.split('\n') if l.strip()]
                    
                    for line in edu_lines:
                        if line.startswith('•') or line.startswith('-'):
                            self._add_bullet_point(doc, line.lstrip('•-*►▪→◆ '))
                        else:
                            para = doc.add_paragraph(line)
                            para.paragraph_format.space_after = Pt(4)
                    
                    doc.add_paragraph()  # Spacing
                    break
            
            # Technical Skills
            for key in ['skills', 'technical_skills', 'competencies']:
                if key in sections_dict and sections_dict[key].strip():
                    self._add_section_header(doc, "TECHNICAL SKILLS")
                    
                    skills_text = sections_dict[key].replace('---', '').strip()
                    if skills_text:
                        para = doc.add_paragraph(skills_text)
                        para.paragraph_format.space_after = Pt(6)
                    
                    doc.add_paragraph()  # Spacing
                    break
            
            # Projects
            for key in ['projects', 'key_projects']:
                if key in sections_dict and sections_dict[key].strip():
                    self._add_section_header(doc, "KEY PROJECTS")
                    
                    proj_text = sections_dict[key]
                    proj_lines = [l.strip() for l in proj_text.split('\n') if l.strip()]
                    
                    for line in proj_lines[:10]:
                        if line.startswith('•') or line.startswith('-'):
                            self._add_bullet_point(doc, line.lstrip('•-*►▪→◆ '))
                        else:
                            para = doc.add_paragraph(line)
                            para.paragraph_format.space_after = Pt(4)
                    
                    doc.add_paragraph()  # Spacing
                    break
            
            # Certifications
            for key in ['certifications', 'certificates']:
                if key in sections_dict and sections_dict[key].strip():
                    self._add_section_header(doc, "CERTIFICATIONS")
                    
                    cert_text = sections_dict[key]
                    cert_lines = [l.strip() for l in cert_text.split('\n') if l.strip()]
                    
                    for line in cert_lines:
                        if line.startswith('•') or line.startswith('-'):
                            self._add_bullet_point(doc, line.lstrip('•-*►▪→◆ '))
                        else:
                            para = doc.add_paragraph(line)
                            para.paragraph_format.space_after = Pt(4)
                    
                    break
            
            # Save document
            doc.save(output_path)
            print(f"[docx] ✅ Resume DOCX generated: {output_path}")
            return True
            
        except Exception as e:
            print(f"[docx] ❌ Error generating resume DOCX: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _add_section_header(self, doc, text: str):
        """Add a formatted section header"""
        para = doc.add_paragraph(text)
        run = para.runs[0]
        run.font.size = Pt(12)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0, 51, 102)  # Dark blue
        para.paragraph_format.space_before = Pt(12)
        para.paragraph_format.space_after = Pt(8)
        # Add bottom border
        para.paragraph_format.left_indent = Pt(0)
    
    def _add_bullet_point(self, doc, text: str):
        """Add a formatted bullet point"""
        para = doc.add_paragraph(text, style='List Bullet')
        para.paragraph_format.space_after = Pt(4)
        para.paragraph_format.left_indent = Inches(0.25)
        run = para.runs[0] if para.runs else None
        if run:
            run.font.size = Pt(10)
    
    def _parse_resume_content(self, content: str) -> dict:
        """Parse resume content into sections"""
        sections = {}
        current_section = None
        current_content = []
        
        lines = content.split('\n')
        
        section_keywords = {
            'contact': ['contact', 'email:', 'phone:', 'github:', 'linkedin:'],
            'summary': ['summary', 'objective', 'profile', 'professional summary'],
            'experience': ['experience', 'employment', 'work history', 'work experience'],
            'education': ['education', 'academic'],
            'skills': ['skills', 'competencies', 'technical skills'],
            'projects': ['projects', 'portfolio', 'key projects'],
            'certifications': ['certifications', 'licenses', 'certificates']
        }
        
        for line in lines:
            line_stripped = line.strip()
            line_lower = line_stripped.lower()
            
            if not current_section and not line_stripped:
                continue
            
            # Check for section headers
            is_section_header = False
            found_section = None
            
            # All-caps headers
            if line_stripped.isupper() and len(line_stripped) > 3:
                for section_key, keywords in section_keywords.items():
                    if any(keyword in line_lower for keyword in keywords):
                        is_section_header = True
                        found_section = section_key
                        break
            
            # Keyword headers
            if not is_section_header:
                for section_key, keywords in section_keywords.items():
                    if any(line_lower.startswith(keyword) or line_lower == keyword for keyword in keywords):
                        is_section_header = True
                        found_section = section_key
                        break
            
            if is_section_header and found_section:
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = found_section
                current_content = []
            elif current_section:
                current_content.append(line)
            else:
                # Contact info detection
                if 'github:' in line_lower or 'linkedin:' in line_lower or '@' in line:
                    if 'contact' not in sections:
                        sections['contact'] = line_stripped
                    else:
                        sections['contact'] += '\n' + line_stripped
        
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _parse_experiences(self, text: str) -> list:
        """Parse work experience into structured format"""
        experiences = []
        current_exp = None
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Company/position line
            if '|' in line or any(keyword in line.lower() for keyword in ['engineer', 'developer', 'manager', 'analyst', 'lead', 'architect', 'scientist', 'consultant']):
                if current_exp and current_exp.get('bullets'):
                    experiences.append(current_exp)
                
                current_exp = {'bullets': []}
                
                if '|' in line:
                    parts = line.split('|')
                    current_exp['position'] = parts[0].strip()
                    if len(parts) > 1:
                        current_exp['company'] = parts[1].strip()
                else:
                    current_exp['position'] = line
            
            # Date/location line
            elif current_exp and any(month in line for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', '20', 'Present']):
                if '|' in line:
                    parts = line.split('|')
                    current_exp['dates'] = parts[0].strip()
                    if len(parts) > 1:
                        current_exp['location'] = parts[1].strip()
                else:
                    current_exp['dates'] = line
            
            # Bullet point
            elif current_exp:
                bullet = line.lstrip('•-*►▪→◆ ')
                if bullet and len(bullet) > 15:
                    current_exp['bullets'].append(bullet)
        
        if current_exp and current_exp.get('bullets'):
            experiences.append(current_exp)
        
        return experiences


# Convenience function
def generate_resume_docx(content: str, output_path: str, **kwargs) -> bool:
    """Generate a resume DOCX"""
    generator = WordDocumentGenerator()
    return generator.generate_resume_docx(content, output_path, **kwargs)

