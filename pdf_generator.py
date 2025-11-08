"""
PDF Generator for Resumes and Cover Letters
Generates professional 2-page resumes and 1-page cover letters in PDF format
"""
import os
from typing import Optional
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from datetime import datetime


class PDFGenerator:
    """Generate professional PDF documents for resumes and cover letters"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for professional formatting"""
        # Header style
        self.styles.add(ParagraphStyle(
            name='CustomHeader',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subheader style
        self.styles.add(ParagraphStyle(
            name='CustomSubHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=8,
            spaceBefore=12,
            fontName='Helvetica-Bold',
            borderWidth=1,
            borderColor=colors.HexColor('#3498db'),
            borderPadding=4,
            backColor=colors.HexColor('#ecf0f1')
        ))
        
        # Contact info style
        self.styles.add(ParagraphStyle(
            name='ContactInfo',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#34495e'),
            alignment=TA_CENTER,
            spaceAfter=12
        ))
        
        # Bullet point style
        self.styles.add(ParagraphStyle(
            name='BulletPoint',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#2c3e50'),
            leftIndent=20,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            bulletIndent=10
        ))
        
        # Company/Position style
        self.styles.add(ParagraphStyle(
            name='CompanyPosition',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=4,
            spaceBefore=8,
            fontName='Helvetica-Bold'
        ))
        
        # Date/Location style
        self.styles.add(ParagraphStyle(
            name='DateLocation',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#7f8c8d'),
            spaceAfter=6,
            fontName='Helvetica-Oblique'
        ))
    
    def generate_resume_pdf(
        self,
        content: str,
        output_path: str,
        job_title: str = "",
        company_name: str = "",
        candidate_name: str = ""
    ) -> bool:
        """
        Generate a professional 2-page resume PDF
        
        Args:
            content: Resume text content
            output_path: Path to save the PDF
            job_title: Target job title
            company_name: Target company name
            candidate_name: Candidate's name
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch
            )
            
            # Build content
            story = []
            
            # Parse and format the resume content
            sections = self._parse_resume_content(content)
            
            # Header with name
            if candidate_name:
                story.append(Paragraph(candidate_name, self.styles['CustomHeader']))
            
            # Contact information
            if 'contact' in sections:
                story.append(Paragraph(sections['contact'], self.styles['ContactInfo']))
            
            # Target position
            if job_title and company_name:
                story.append(Paragraph(
                    f"<b>Target Position:</b> {job_title} at {company_name}",
                    self.styles['Normal']
                ))
                story.append(Spacer(1, 0.2*inch))
            
            # Professional Summary (10 bullet points)
            if 'summary' in sections or 'professional_summary' in sections:
                story.append(Paragraph("PROFESSIONAL SUMMARY", self.styles['CustomSubHeader']))
                summary_text = sections.get('summary', sections.get('professional_summary', ''))
                summary_bullets = self._extract_bullet_points(summary_text, max_bullets=10)
                for bullet in summary_bullets:
                    story.append(Paragraph(f"• {bullet}", self.styles['BulletPoint']))
                story.append(Spacer(1, 0.15*inch))
            
            # Work Experience (most recent, relevant to job)
            if 'experience' in sections or 'work_experience' in sections:
                story.append(Paragraph("WORK EXPERIENCE", self.styles['CustomSubHeader']))
                exp_text = sections.get('experience', sections.get('work_experience', ''))
                experiences = self._parse_experiences(exp_text)
                
                for exp in experiences[:3]:  # Show top 3 most recent/relevant
                    # Company and position
                    story.append(Paragraph(
                        f"<b>{exp.get('position', 'Position')}</b> | {exp.get('company', 'Company')}",
                        self.styles['CompanyPosition']
                    ))
                    # Date and location
                    date_loc = []
                    if exp.get('dates'):
                        date_loc.append(exp['dates'])
                    if exp.get('location'):
                        date_loc.append(exp['location'])
                    if date_loc:
                        story.append(Paragraph(' | '.join(date_loc), self.styles['DateLocation']))
                    
                    # Key achievements/responsibilities
                    for bullet in exp.get('bullets', []):
                        story.append(Paragraph(f"• {bullet}", self.styles['BulletPoint']))
                    
                    story.append(Spacer(1, 0.1*inch))
            
            # Education
            if 'education' in sections:
                story.append(Paragraph("EDUCATION", self.styles['CustomSubHeader']))
                story.append(Paragraph(sections['education'], self.styles['Normal']))
                story.append(Spacer(1, 0.15*inch))
            
            # Skills
            if 'skills' in sections or 'technical_skills' in sections:
                story.append(Paragraph("TECHNICAL SKILLS", self.styles['CustomSubHeader']))
                skills_text = sections.get('skills', sections.get('technical_skills', ''))
                story.append(Paragraph(skills_text, self.styles['Normal']))
                story.append(Spacer(1, 0.15*inch))
            
            # Projects (if space allows)
            if 'projects' in sections:
                story.append(Paragraph("KEY PROJECTS", self.styles['CustomSubHeader']))
                story.append(Paragraph(sections['projects'], self.styles['Normal']))
                story.append(Spacer(1, 0.15*inch))
            
            # Certifications
            if 'certifications' in sections:
                story.append(Paragraph("CERTIFICATIONS", self.styles['CustomSubHeader']))
                story.append(Paragraph(sections['certifications'], self.styles['Normal']))
            
            # Build PDF
            doc.build(story)
            print(f"[pdf] ✅ Resume PDF generated: {output_path}")
            return True
            
        except Exception as e:
            print(f"[pdf] ❌ Error generating resume PDF: {e}")
            return False
    
    def generate_cover_letter_pdf(
        self,
        content: str,
        output_path: str,
        job_title: str = "",
        company_name: str = "",
        candidate_name: str = "",
        candidate_email: str = "",
        candidate_phone: str = ""
    ) -> bool:
        """
        Generate a professional 1-page cover letter PDF
        
        Args:
            content: Cover letter text content
            output_path: Path to save the PDF
            job_title: Target job title
            company_name: Target company name
            candidate_name: Candidate's name
            candidate_email: Candidate's email
            candidate_phone: Candidate's phone
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=inch,
                leftMargin=inch,
                topMargin=inch,
                bottomMargin=inch
            )
            
            story = []
            
            # Header with contact info
            if candidate_name:
                story.append(Paragraph(candidate_name, self.styles['CustomHeader']))
            
            contact_parts = []
            if candidate_email:
                contact_parts.append(candidate_email)
            if candidate_phone:
                contact_parts.append(candidate_phone)
            if contact_parts:
                story.append(Paragraph(' | '.join(contact_parts), self.styles['ContactInfo']))
            
            # Date
            story.append(Paragraph(
                datetime.now().strftime("%B %d, %Y"),
                self.styles['Normal']
            ))
            story.append(Spacer(1, 0.2*inch))
            
            # Hiring manager address
            if company_name:
                story.append(Paragraph(f"Hiring Manager<br/>{company_name}", self.styles['Normal']))
                story.append(Spacer(1, 0.2*inch))
            
            # Subject line
            if job_title and company_name:
                story.append(Paragraph(
                    f"<b>Re: Application for {job_title} Position</b>",
                    self.styles['Normal']
                ))
                story.append(Spacer(1, 0.2*inch))
            
            # Cover letter body
            # Parse paragraphs and format
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            for para in paragraphs:
                # Skip if it looks like a header or signature
                if para.lower().startswith(('dear', 'sincerely', 'best regards')):
                    story.append(Paragraph(para, self.styles['Normal']))
                else:
                    story.append(Paragraph(para, self.styles['BodyText']))
                story.append(Spacer(1, 0.15*inch))
            
            # Closing
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph("Sincerely,", self.styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
            if candidate_name:
                story.append(Paragraph(candidate_name, self.styles['Normal']))
            
            # Build PDF
            doc.build(story)
            print(f"[pdf] ✅ Cover letter PDF generated: {output_path}")
            return True
            
        except Exception as e:
            print(f"[pdf] ❌ Error generating cover letter PDF: {e}")
            return False
    
    def _parse_resume_content(self, content: str) -> dict:
        """Parse resume text content into sections"""
        sections = {}
        current_section = None
        current_content = []
        
        lines = content.split('\n')
        
        # Common section headers
        section_keywords = {
            'contact': ['contact', 'email', 'phone', 'address'],
            'summary': ['summary', 'objective', 'profile'],
            'professional_summary': ['professional summary'],
            'experience': ['experience', 'employment', 'work history'],
            'work_experience': ['work experience'],
            'education': ['education', 'academic'],
            'skills': ['skills', 'competencies'],
            'technical_skills': ['technical skills'],
            'projects': ['projects', 'portfolio'],
            'certifications': ['certifications', 'licenses']
        }
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Check if this is a section header
            found_section = None
            for section_key, keywords in section_keywords.items():
                if any(keyword in line_lower for keyword in keywords):
                    # Save previous section
                    if current_section and current_content:
                        sections[current_section] = '\n'.join(current_content).strip()
                    
                    found_section = section_key
                    current_section = section_key
                    current_content = []
                    break
            
            if not found_section and current_section:
                current_content.append(line)
        
        # Save last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        # If no sections found, treat entire content as summary
        if not sections:
            sections['summary'] = content
        
        return sections
    
    def _extract_bullet_points(self, text: str, max_bullets: int = 10) -> list:
        """Extract bullet points from text"""
        bullets = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            # Remove existing bullet characters
            line = line.lstrip('•-*►▪→◆ ')
            if line and len(line) > 10:  # Meaningful content
                bullets.append(line)
                if len(bullets) >= max_bullets:
                    break
        
        return bullets
    
    def _parse_experiences(self, text: str) -> list:
        """Parse work experience section into structured data"""
        experiences = []
        current_exp = None
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this looks like a company/position line
            if '|' in line or (any(keyword in line.lower() for keyword in ['engineer', 'developer', 'manager', 'analyst', 'lead', 'architect'])):
                # Save previous experience
                if current_exp and current_exp.get('bullets'):
                    experiences.append(current_exp)
                
                # Start new experience
                current_exp = {'bullets': []}
                
                # Parse company and position
                if '|' in line:
                    parts = line.split('|')
                    current_exp['position'] = parts[0].strip()
                    if len(parts) > 1:
                        current_exp['company'] = parts[1].strip()
                else:
                    current_exp['position'] = line
            
            # Check if this looks like a date/location line
            elif current_exp and any(month in line for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', '20']):
                if '|' in line:
                    parts = line.split('|')
                    current_exp['dates'] = parts[0].strip()
                    if len(parts) > 1:
                        current_exp['location'] = parts[1].strip()
                else:
                    current_exp['dates'] = line
            
            # Otherwise, it's probably a bullet point
            elif current_exp:
                bullet = line.lstrip('•-*►▪→◆ ')
                if bullet and len(bullet) > 15:  # Meaningful content
                    current_exp['bullets'].append(bullet)
        
        # Save last experience
        if current_exp and current_exp.get('bullets'):
            experiences.append(current_exp)
        
        return experiences


# Convenience functions
def generate_resume_pdf(content: str, output_path: str, **kwargs) -> bool:
    """Generate a resume PDF"""
    generator = PDFGenerator()
    return generator.generate_resume_pdf(content, output_path, **kwargs)


def generate_cover_letter_pdf(content: str, output_path: str, **kwargs) -> bool:
    """Generate a cover letter PDF"""
    generator = PDFGenerator()
    return generator.generate_cover_letter_pdf(content, output_path, **kwargs)

