"""
Create a class that generates a resume and cover letter based on job description.
Adapted for the job matcher pipeline.
"""
import os
import textwrap
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Any

# Load environment variables from .env file
load_dotenv()


class LLMResumer:
    def __init__(self, openai_api_key: str = None):
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key required")
        
        self.llm = ChatOpenAI(
            model_name="gpt-4o-mini",
            openai_api_key=api_key,
            temperature=0.4
        )
        self.resume_data = None

    @staticmethod
    def _preprocess_template_string(template: str) -> str:
        """Remove leading whitespace and indentation."""
        return textwrap.dedent(template)

    def set_resume_data(self, resume_text: str) -> None:
        """Set the resume text to be used for generation."""
        self.resume_data = resume_text

    def generate_tailored_resume(
        self,
        job_description: str,
        company: str,
        role: str
    ) -> str:
        """
        Generate a tailored resume based on job description.
        
        Args:
            job_description: The job description text
            company: Company name
            role: Role title
            
        Returns:
            str: Tailored resume text
        """
        prompt_template = self._preprocess_template_string("""
        You are an expert resume writer specializing in ATS optimization.
        
        Given a resume and job description, rewrite the resume to highlight relevant skills,
        experience, and keywords that align with the job requirements while maintaining truthfulness.
        
        Company: {company}
        Role: {role}
        
        Job Description:
        {job_description}
        
        Current Resume:
        {resume}
        
        Task: Rewrite the resume to emphasize skills and experience matching the job description.
        Keep the same structure and facts; optimize keyword placement for ATS.
        Output plain text only, well-formatted and professional.
        """)
        
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm | StrOutputParser()
        
        output = chain.invoke({
            "company": company,
            "role": role,
            "job_description": job_description,
            "resume": self.resume_data
        })
        
        return output

    def generate_cover_letter(
        self,
        job_description: str,
        company: str,
        role: str
    ) -> str:
        """
        Generate a cover letter for a specific job.
        
        Args:
            job_description: The job description text
            company: Company name
            role: Role title
            
        Returns:
            str: Cover letter text (3 paragraphs, no greeting/signature)
        """
        prompt_template = self._preprocess_template_string("""
        You are an expert technical recruiter and writing assistant.
        
        Write a concise three-paragraph cover letter without greeting or signature.
        Tone: professional, conversational, natural. Use the resume strengths and job requirements.
        
        Company: {company}
        Role: {role}
        
        Job Description:
        {job_description}
        
        Resume:
        {resume}
        
        Rules:
        - Three short paragraphs
        - No greeting or signature
        - Reference concrete skills and outcomes that align with the role
        - Avoid placeholders; write as final text
        - Be specific and impactful
        """)
        
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm | StrOutputParser()
        
        output = chain.invoke({
            "company": company,
            "role": role,
            "job_description": job_description,
            "resume": self.resume_data
        })
        
        return output

    def generate_resume_and_cover_letter(
        self,
        job_description: str,
        company: str,
        role: str
    ) -> Dict[str, str]:
        """
        Generate both resume and cover letter in parallel.
        
        Args:
            job_description: The job description text
            company: Company name
            role: Role title
            
        Returns:
            dict: {"resume": str, "cover_letter": str}
        """
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
                "cover_letter": cover_letter_future.result()
            }
