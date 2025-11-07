"""
Unified job application generator using LangChain LLM modules.
Integrates job parser, resume generator, and cover letter generator.
"""
import os
import textwrap
from pathlib import Path
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor

try:
    import openai_compat  # noqa: F401
except Exception:
    openai_compat = None

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()


class JobApplicationGenerator:
    """
    Unified class that generates tailored resume and cover letter from job description.
    Simplifies the original multi-file structure for our use case.
    """
    
    def __init__(self, openai_api_key: str = None):
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key required")
        
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=api_key,
            temperature=0.4
        )
        self.resume_text = None

    @staticmethod
    def _preprocess_template(template: str) -> str:
        """Remove leading whitespace and indentation."""
        return textwrap.dedent(template)

    def set_resume(self, resume_text: str) -> None:
        """Set the resume text to be used for generation."""
        self.resume_text = resume_text

    def summarize_job_description(self, job_description: str) -> str:
        """
        Summarize job description to extract key requirements.
        Based on llm_job_parser functionality.
        """
        template = self._preprocess_template("""
        You are an expert at analyzing job descriptions.
        Extract and summarize the key information from this job description:
        
        - Role/Title
        - Key Responsibilities (top 5)
        - Required Skills and Qualifications
        - Preferred/Nice-to-have Skills
        - Company Culture/Values (if mentioned)
        
        Job Description:
        {text}
        
        Provide a concise, structured summary.
        """)
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm | StrOutputParser()
        return chain.invoke({"text": job_description})

    def generate_tailored_resume(
        self,
        job_description: str,
        company: str,
        role: str
    ) -> str:
        """
        Generate ATS-optimized resume tailored to job description.
        Based on llm_generate_resume_from_job functionality.
        """
        # First summarize the job description
        jd_summary = self.summarize_job_description(job_description)
        
        template = self._preprocess_template("""
        You are an expert resume writer specializing in ATS optimization.
        
        Task: Rewrite the resume below to align with the job requirements while maintaining truthfulness.
        
        **Company**: {company}
        **Role**: {role}
        
        **Job Requirements Summary**:
        {job_summary}
        
        **Current Resume**:
        {resume}
        
        **Instructions**:
        1. Highlight experiences and skills that match the job requirements
        2. Use keywords from the job description naturally
        3. Quantify achievements where possible
        4. Reorder or emphasize relevant sections
        5. Keep the same factual information - DO NOT fabricate
        6. Maintain professional formatting
        7. Optimize for ATS scanning
        
        Output a well-structured, ATS-friendly resume in plain text format.
        """)
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm | StrOutputParser()
        
        return chain.invoke({
            "company": company,
            "role": role,
            "job_summary": jd_summary,
            "resume": self.resume_text
        })

    def generate_cover_letter(
        self,
        job_description: str,
        company: str,
        role: str
    ) -> str:
        """
        Generate compelling cover letter based on job description and resume.
        Based on llm_generate_cover_letter_from_job functionality.
        """
        # First summarize the job description
        jd_summary = self.summarize_job_description(job_description)
        
        template = self._preprocess_template("""
        You are an expert cover letter writer.
        
        Write a professional, compelling cover letter for this job application.
        
        **Company**: {company}
        **Role**: {role}
        
        **Job Requirements**:
        {job_summary}
        
        **Candidate's Resume**:
        {resume}
        
        **Instructions**:
        1. Write 3-4 concise paragraphs
        2. No greeting or signature (just body)
        3. Open with why you're excited about this specific role and company
        4. Highlight 2-3 relevant achievements from the resume that match job requirements
        5. Show understanding of the company's needs and how you can address them
        6. Close with enthusiasm and call to action
        7. Professional yet conversational tone
        8. Use specific examples, avoid generic statements
        
        Output only the cover letter body (no "Dear..." or "Sincerely").
        """)
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm | StrOutputParser()
        
        return chain.invoke({
            "company": company,
            "role": role,
            "job_summary": jd_summary,
            "resume": self.resume_text
        })

    def generate_application_package(
        self,
        job_description: str,
        company: str,
        role: str,
        parallel: bool = True
    ) -> Dict[str, str]:
        """
        Generate both tailored resume and cover letter.
        
        Args:
            job_description: Full job description text
            company: Company name
            role: Role/title
            parallel: Generate resume and cover letter in parallel (faster)
        
        Returns:
            dict: {"resume": str, "cover_letter": str, "job_summary": str}
        """
        # Always generate job summary first
        job_summary = self.summarize_job_description(job_description)
        
        if parallel:
            # Generate resume and cover letter in parallel
            with ThreadPoolExecutor(max_workers=2) as executor:
                resume_future = executor.submit(
                    self.generate_tailored_resume,
                    job_description,
                    company,
                    role
                )
                cover_letter_future = executor.submit(
                    self.generate_cover_letter,
                    job_description,
                    company,
                    role
                )
                
                return {
                    "resume": resume_future.result(),
                    "cover_letter": cover_letter_future.result(),
                    "job_summary": job_summary
                }
        else:
            # Sequential generation
            return {
                "resume": self.generate_tailored_resume(job_description, company, role),
                "cover_letter": self.generate_cover_letter(job_description, company, role),
                "job_summary": job_summary
            }

