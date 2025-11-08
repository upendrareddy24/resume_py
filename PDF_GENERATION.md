# 📄 PDF Resume & Cover Letter Generation

## Overview

The job matcher now automatically generates **professional PDF versions** of all resumes and cover letters in addition to the text versions.

## Features

### ✅ 2-Page Professional Resumes
- **10-bullet Professional Summary** highlighting most relevant skills and achievements
- **Most Recent Relevant Experience** prioritized for the target role
- **Quantifiable results** and impact metrics
- **ATS-optimized formatting** with clear section headers
- **Clean, modern design** with professional styling

### ✅ 1-Page Cover Letters
- **Personalized content** tailored to each company and role
- **Compelling hook** showing genuine interest
- **Specific examples** with quantifiable results
- **Professional formatting** with proper spacing and layout

### ✅ Automatic PDF Generation
- PDFs generated automatically alongside text files
- No additional user action required
- Exported to the same directories (`output/cover_letters/`, `output/tailored_resumes/`)

## Output Structure

```
output/
├── cover_letters/
│   ├── cover_Google_Senior_Engineer.txt     ← Text version
│   ├── cover_Google_Senior_Engineer.pdf     ← PDF version
│   ├── cover_Amazon_SDE.txt
│   ├── cover_Amazon_SDE.pdf
│   └── ...
├── tailored_resumes/
│   ├── resume_Google_Senior_Engineer.txt    ← Text version
│   ├── resume_Google_Senior_Engineer.pdf    ← PDF version
│   ├── resume_Amazon_SDE.txt
│   ├── resume_Amazon_SDE.pdf
│   └── ...
└── job_summaries/
    └── ...
```

## Resume Format

### Professional Summary (10 Bullets)
```
• Led cross-functional team of 12 engineers to deliver cloud migration, reducing costs by 40% ($2M annually)
• Architected microservices platform serving 50M+ DAU with 99.99% uptime
• Optimized database queries reducing latency from 2s to 200ms (90% improvement)
• Implemented CI/CD pipeline cutting deployment time from 4 hours to 15 minutes
• Mentored 8 junior engineers, with 6 promoted within 18 months
• Designed fault-tolerant system processing 10TB+ daily data with zero downtime
• Led migration to Kubernetes, improving resource utilization by 65%
• Developed ML pipeline increasing prediction accuracy from 75% to 94%
• Established engineering best practices adopted across 3 teams (30+ engineers)
• Published 2 technical papers at top-tier conferences with 150+ citations
```

### Work Experience (Most Recent & Relevant)
- **2-3 most recent positions** that align with job requirements
- **4-6 impactful bullet points** per position with:
  - Strong action verbs (Led, Architected, Implemented, Optimized)
  - Quantifiable results (%, $, time saved, users impacted)
  - Technologies mentioned in job description
  - Increasing responsibility and impact

### Additional Sections
- **Technical Skills**: Organized by category
- **Education**: Degree, institution, GPA (if >3.5)
- **Projects**: 2-3 impressive projects (if space allows)
- **Certifications**: Industry-recognized certifications

## Cover Letter Format

### Structure
1. **Opening Paragraph**: Hook + Why this company + Why this role
2. **Body Paragraphs (2-3)**: Relevant achievements with specific examples
3. **Closing Paragraph**: Value proposition + Next steps

### Tone
- Professional yet personable
- Confident without arrogance
- Enthusiastic about the opportunity
- Matches company culture (formal for enterprise, casual for startups)

## Technical Details

### PDF Generator (`pdf_generator.py`)
- Built on **ReportLab** library
- Professional styling with custom paragraph styles
- Intelligent content parsing and formatting
- Automatic section detection
- Graceful error handling

### Resume Prompt (`enhanced_prompts.py`)
```python
ENHANCED_RESUME_PROMPT = """
Requirements:
1. 2-PAGE professional resume tailored for specific role
2. PROFESSIONAL SUMMARY with EXACTLY 10 bullet points
3. WORK EXPERIENCE: Most recent and relevant positions
4. Quantifiable results and impact metrics
5. ATS-optimized formatting
"""
```

### Integration Points

#### 1. JobApplicationGenerator Path
```python
if use_job_app_gen and auto_tailor and jd_text:
    result = job_app_gen.generate_application_package(...)
    
    # Save TXT
    resume_path = tailored_resumes_dir / f"resume_{base}.txt"
    with open(resume_path, "w") as f:
        f.write(result["resume"])
    
    # Generate PDF
    from pdf_generator import generate_resume_pdf
    pdf_path = tailored_resumes_dir / f"resume_{base}.pdf"
    generate_resume_pdf(
        content=result["resume"],
        output_path=str(pdf_path),
        job_title=role,
        company_name=company
    )
```

#### 2. LLMResumer Path
```python
if use_llm_resumer and auto_tailor and jd_text:
    resume_text_llm = llm_resumer.generate_tailored_resume(...)
    
    # Save TXT
    resume_path = tailored_resumes_dir / f"resume_{base}.txt"
    with open(resume_path, "w") as f:
        f.write(resume_text_llm)
    
    # Generate PDF
    from pdf_generator import generate_resume_pdf
    pdf_path = tailored_resumes_dir / f"resume_{base}.pdf"
    generate_resume_pdf(
        content=resume_text_llm,
        output_path=str(pdf_path),
        job_title=role,
        company_name=company
    )
```

## Configuration

### Requirements
Add to `requirements.txt`:
```
reportlab==4.2.5
```

### Install
```bash
pip install reportlab==4.2.5
```

## Usage

### Local Testing
```bash
# Run matcher with PDF generation
python match.py --config config.json

# Check output
ls -lh output/tailored_resumes/*.pdf
ls -lh output/cover_letters/*.pdf
```

### GitHub Actions
The workflow automatically:
1. Generates PDFs for all resumes and cover letters
2. Uploads them as artifacts
3. Reports counts in job summary

Expected output in GitHub Actions:
```
## 📁 Generated Files

- **Cover Letters (TXT)**: 35
- **Cover Letters (PDF)**: 35
- **Tailored Resumes (TXT)**: 35
- **Tailored Resumes (PDF)**: 35
- **Parsed Jobs**: 35
- **Job Summaries**: 35
```

## Error Handling

### PDF Generation Failure
If PDF generation fails, the text file is still saved:
```
[jobgen] ✅ Resume saved: resume_Google_Senior_Engineer.txt
[jobgen] ⚠️  PDF generation failed: [error details]
```

The pipeline continues without interruption.

### Common Issues

#### Issue: `ModuleNotFoundError: No module named 'reportlab'`
**Solution**: Install reportlab
```bash
pip install reportlab==4.2.5
```

#### Issue: PDF looks incorrect
**Solution**: Check the text content format. The PDF generator expects:
- Clear section headers (e.g., "PROFESSIONAL SUMMARY", "WORK EXPERIENCE")
- Bullet points with `•` character
- Proper line breaks between sections

#### Issue: PDF is blank or incomplete
**Solution**: Check that the text content has meaningful data (not just "Position: X at Y")

## Example Output

### Resume PDF Features
✅ **Header**
```
JOHN DOE
john.doe@email.com | (555) 123-4567
linkedin.com/in/johndoe | github.com/johndoe

Target Position: Senior Software Engineer at Google
```

✅ **Professional Summary**
```
PROFESSIONAL SUMMARY

• Led development of distributed systems serving 100M+ users with 99.99% uptime
• Architected microservices platform reducing deployment time by 80% (4h → 48min)
... (8 more bullets)
```

✅ **Work Experience**
```
WORK EXPERIENCE

Senior Software Engineer | Tech Company Inc.
Jan 2020 - Present | San Francisco, CA
• Led team of 8 engineers to deliver cloud migration, saving $3M annually
• Architected fault-tolerant system processing 5TB+ daily with zero data loss
• Implemented ML pipeline increasing prediction accuracy from 70% to 92%
• Optimized API response time from 800ms to 80ms (90% improvement)
```

### Cover Letter PDF Features
✅ **Professional Layout**
```
JOHN DOE
john.doe@email.com | (555) 123-4567

November 8, 2025

Hiring Manager
Google

Re: Application for Senior Software Engineer Position

Dear Hiring Manager,

I am excited to apply for the Senior Software Engineer position at Google...

[Compelling content with specific examples and quantifiable results]

Sincerely,

John Doe
```

## Benefits

### For Job Seekers
- ✅ Professional, ATS-optimized resumes
- ✅ Tailored to each specific role
- ✅ Ready to upload to job portals
- ✅ Both text and PDF formats available
- ✅ Consistent formatting across all applications

### For the System
- ✅ Automated PDF generation (no manual work)
- ✅ Graceful error handling (doesn't break the pipeline)
- ✅ Consistent branding and formatting
- ✅ Easy to customize styling
- ✅ Works with all generation methods (JobAppGen, LLMResumer, etc.)

## Future Enhancements

Potential improvements:
- [ ] Add customizable templates
- [ ] Support for different resume formats (chronological, functional, hybrid)
- [ ] Include candidate photo (optional)
- [ ] Add QR code linking to portfolio/LinkedIn
- [ ] Multi-language support
- [ ] Custom color schemes per company
- [ ] Watermark support
- [ ] Digital signature integration

## Files Involved

| File | Purpose |
|------|---------|
| `pdf_generator.py` | Core PDF generation logic |
| `enhanced_prompts.py` | Enhanced prompts for resume/cover letter content |
| `match.py` | Integration of PDF generation into workflow |
| `requirements.txt` | Added reportlab dependency |
| `.github/workflows/job-matcher.yml` | Updated to report PDF counts |

## Summary

The PDF generation feature provides:
- **Professional, ATS-optimized 2-page resumes** with 10-bullet summaries
- **Compelling 1-page cover letters** tailored to each role
- **Automatic generation** alongside text files
- **Robust error handling** that doesn't break the pipeline
- **Ready-to-use** format for job applications

All resumes prioritize **most recent and relevant experience** for the target role, ensuring maximum impact! 🎯

