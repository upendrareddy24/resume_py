"""
Resume Upload Helper - Adapted from Job_search_agent
Creates and saves resume PDFs and DOCX files in the proper format for job applications
"""
import os
import time
import base64
import traceback
from pathlib import Path
from typing import Optional
from pdf_generator import generate_resume_pdf, generate_cover_letter_pdf
from docx_generator import generate_resume_docx


def create_and_save_resume_files(
    resume_text: str,
    output_dir: str,
    job_title: str,
    company_name: str,
    candidate_name: str = "",
    timestamp: Optional[int] = None,
    formats: list = ['pdf', 'docx']
) -> dict:
    """
    Create and save resume in multiple formats (PDF and DOCX).
    
    Args:
        resume_text: The resume content as text
        output_dir: Directory to save the files
        job_title: Target job title
        company_name: Target company name
        candidate_name: Candidate's name
        timestamp: Optional timestamp for filename
        formats: List of formats to generate ('pdf', 'docx')
    
    Returns:
        dict: Paths to created files {'pdf': path, 'docx': path}
    """
    paths = {}
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate timestamp
        if timestamp is None:
            timestamp = int(time.time())
        
        # Sanitize company and job title for filename
        safe_company = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_'))[:30]
        safe_title = "".join(c for c in job_title if c.isalnum() or c in (' ', '-', '_'))[:30]
        
        base_filename = f"resume_{safe_company}_{safe_title}_{timestamp}"
        
        print(f"  [resume] Generating files for {company_name} - {job_title}")
        
        # Generate DOCX (preferred format - better formatting control)
        if 'docx' in formats:
            docx_filename = f"{base_filename}.docx"
            docx_path = os.path.join(output_dir, docx_filename)
            
            success = generate_resume_docx(
                content=resume_text,
                output_path=docx_path,
                job_title=job_title,
                company_name=company_name,
                candidate_name=candidate_name
            )
            
            if success and os.path.exists(docx_path):
                file_size = os.path.getsize(docx_path)
                abs_path = os.path.abspath(docx_path)
                paths['docx'] = abs_path
                print(f"  [resume] ✅ DOCX created: {docx_filename} ({file_size} bytes)")
            else:
                print(f"  [resume] ⚠️  DOCX generation failed")
        
        # Generate PDF (for compatibility)
        if 'pdf' in formats:
            pdf_filename = f"{base_filename}.pdf"
            pdf_path = os.path.join(output_dir, pdf_filename)
            
            success = generate_resume_pdf(
                content=resume_text,
                output_path=pdf_path,
                job_title=job_title,
                company_name=company_name,
                candidate_name=candidate_name
            )
            
            if success and os.path.exists(pdf_path):
                file_size = os.path.getsize(pdf_path)
                abs_path = os.path.abspath(pdf_path)
                paths['pdf'] = abs_path
                print(f"  [resume] ✅ PDF created: {pdf_filename} ({file_size} bytes)")
            else:
                print(f"  [resume] ⚠️  PDF generation failed")
        
        # Validate files
        for format_type, file_path in paths.items():
            if not validate_file(file_path):
                print(f"  [resume] ⚠️  {format_type.upper()} validation warning for {os.path.basename(file_path)}")
        
        return paths
        
    except Exception as e:
        print(f"  [resume] ❌ Error creating resume files: {e}")
        traceback.print_exc()
        return paths


def create_and_save_cover_letter_pdf(
    cover_letter_text: str,
    output_dir: str,
    job_title: str,
    company_name: str,
    candidate_name: str = "",
    candidate_email: str = "",
    candidate_phone: str = "",
    timestamp: Optional[int] = None
) -> Optional[str]:
    """
    Create and save a cover letter PDF file.
    
    Args:
        cover_letter_text: The cover letter content as text
        output_dir: Directory to save the PDF
        job_title: Target job title
        company_name: Target company name
        candidate_name: Candidate's name
        candidate_email: Candidate's email
        candidate_phone: Candidate's phone
        timestamp: Optional timestamp for filename
    
    Returns:
        str: Absolute path to the created PDF file, or None if failed
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename with timestamp
        if timestamp is None:
            timestamp = int(time.time())
        
        # Sanitize company and job title for filename
        safe_company = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_'))[:30]
        safe_title = "".join(c for c in job_title if c.isalnum() or c in (' ', '-', '_'))[:30]
        
        filename = f"cover_{safe_company}_{safe_title}_{timestamp}.pdf"
        file_path = os.path.join(output_dir, filename)
        
        print(f"  [cover] Generating PDF for {company_name} - {job_title}")
        
        # Generate PDF
        success = generate_cover_letter_pdf(
            content=cover_letter_text,
            output_path=file_path,
            job_title=job_title,
            company_name=company_name,
            candidate_name=candidate_name,
            candidate_email=candidate_email,
            candidate_phone=candidate_phone
        )
        
        if not success:
            print(f"  [cover] ❌ Failed to generate PDF")
            return None
        
        # Validate file was created
        if not os.path.exists(file_path):
            print(f"  [cover] ❌ PDF file not found after generation")
            return None
        
        # Check file size
        file_size = os.path.getsize(file_path)
        max_file_size = 2 * 1024 * 1024  # 2 MB
        
        if file_size > max_file_size:
            print(f"  [cover] ⚠️  Warning: Cover letter file size ({file_size} bytes) exceeds 2 MB")
        
        if file_size < 500:  # Less than 500 bytes is suspicious
            print(f"  [cover] ⚠️  Warning: Cover letter file size is very small ({file_size} bytes)")
        
        abs_path = os.path.abspath(file_path)
        print(f"  [cover] ✅ PDF created successfully: {filename} ({file_size} bytes)")
        
        return abs_path
        
    except Exception as e:
        print(f"  [cover] ❌ Error creating cover letter PDF: {e}")
        traceback.print_exc()
        return None


def validate_file(file_path: str) -> bool:
    """
    Validate a file meets basic requirements for job applications.
    
    Args:
        file_path: Path to the file
    
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        # Check file exists
        if not os.path.exists(file_path):
            print(f"  [validate] ❌ File not found: {file_path}")
            return False
        
        # Check file extension
        allowed_extensions = {".pdf", ".doc", ".docx"}
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension not in allowed_extensions:
            print(f"  [validate] ❌ Invalid file extension: {file_extension}")
            print(f"  [validate] Allowed: {', '.join(allowed_extensions)}")
            return False
        
        # Check file size
        file_size = os.path.getsize(file_path)
        max_file_size = 2 * 1024 * 1024  # 2 MB
        
        if file_size > max_file_size:
            print(f"  [validate] ⚠️  Warning: File too large: {file_size} bytes (max: {max_file_size})")
            return True  # Warning, not error
        
        if file_size < 100:
            print(f"  [validate] ❌ File too small: {file_size} bytes")
            return False
        
        return True
        
    except Exception as e:
        print(f"  [validate] ❌ Error validating file: {e}")
        return False

