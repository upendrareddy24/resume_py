"""
Adapted LLMCoverLetterJobDescription for the job matcher pipeline.
Generates cover letters based on job description and resume using LangChain.
"""
import os
import textwrap
from pathlib import Path
from typing import Optional

try:
    import openai_compat  # noqa: F401
except Exception:
    openai_compat = None

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()


class LLMCoverLetterJobDescription:
    """
    Generate cover letters matching job description and resume.
    Adapted from llm_generate_cover_letter_from_job.py
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
        self.llm_embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=api_key,
        )
        self.resume: Optional[str] = None
        self.job_description: Optional[str] = None

    @staticmethod
    def _preprocess_template_string(template: str) -> str:
        """Remove leading whitespace and indentation."""
        return textwrap.dedent(template)

    def set_resume(self, resume: str) -> None:
        """Set the resume text to be used for generating the cover letter."""
        self.resume = resume

    def set_job_description_from_text(self, job_description_text: str) -> None:
        """
        Set and summarize the job description for cover letter generation.
        """
        summarize_template = self._preprocess_template_string("""
        You are an expert at analyzing job descriptions.
        
        Summarize the following job description, extracting:
        - Key responsibilities (top 3-5)
        - Required qualifications and skills
        - Company culture/values (if mentioned)
        - What makes this role unique or appealing
        
        Keep it concise but comprehensive.
        
        Job Description:
        {text}
        
        Summary:
        """)
        
        prompt = ChatPromptTemplate.from_template(summarize_template)
        chain = prompt | self.llm | StrOutputParser()
        self.job_description = chain.invoke({"text": job_description_text})

    def generate_cover_letter(self) -> str:
        """
        Generate the cover letter based on the job description and resume.
        
        Returns:
            str: The generated cover letter (body only, no greeting/signature)
        """
        if not self.resume:
            raise ValueError("Resume not set. Call set_resume() first.")
        if not self.job_description:
            raise ValueError("Job description not set. Call set_job_description_from_text() first.")
        
        cover_letter_template = self._preprocess_template_string("""
        You are an expert cover letter writer specializing in creating compelling, 
        personalized cover letters that highlight candidate strengths.
        
        **Job Requirements Summary**:
        {job_description}
        
        **Candidate's Resume**:
        {resume}
        
        **Instructions**:
        Write a professional cover letter body (3-4 paragraphs, no greeting or signature) that:
        
        1. **Opening**: Express genuine enthusiasm for the specific role and company. 
           Show you understand what they're looking for.
        
        2. **Body (2 paragraphs)**: 
           - Highlight 2-3 specific achievements from the resume that directly align with job requirements
           - Use concrete examples and metrics where possible
           - Show how your experience solves their specific needs
           - Demonstrate cultural fit and understanding of company values
        
        3. **Closing**: 
           - Reiterate enthusiasm and fit
           - Include a call to action (e.g., "I'd welcome the opportunity to discuss...")
           - End confidently but professionally
        
        **Style Guidelines**:
        - Professional yet conversational tone
        - No generic statements or clichés
        - Specific to THIS job, not a template
        - Action-oriented language
        - 3-4 short paragraphs maximum
        - NO greeting (no "Dear...") or signature (no "Sincerely...")
        - Focus on value you bring, not just what you want
        
        Cover Letter Body:
        """)
        
        prompt = ChatPromptTemplate.from_template(cover_letter_template)
        chain = prompt | self.llm | StrOutputParser()
        
        output = chain.invoke({
            "job_description": self.job_description,
            "resume": self.resume
        })
        
        return output.strip()
    
    def generate_from_job_and_resume(
        self,
        job_description_text: str,
        resume_text: str
    ) -> str:
        """
        Convenience method to generate cover letter in one call.
        
        Args:
            job_description_text: Full job description
            resume_text: Full resume text
            
        Returns:
            str: Generated cover letter body
        """
        self.set_resume(resume_text)
        self.set_job_description_from_text(job_description_text)
        return self.generate_cover_letter()


