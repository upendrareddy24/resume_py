"""
Adapted LLMParser for the job matcher pipeline.
Parses and extracts structured information from job descriptions using LangChain and FAISS.
"""
import os
import tempfile
import textwrap
import re
from pathlib import Path
from typing import Dict, Optional
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import TokenTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader
from dotenv import load_dotenv

load_dotenv()


class LLMParser:
    """
    Parse job descriptions and extract structured information using RAG (Retrieval Augmented Generation).
    Adapted from llm_job_parser.py
    """
    
    def __init__(self, openai_api_key: str = None):
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key required")
        
        self.llm = ChatOpenAI(
            model_name="gpt-4o-mini",
            openai_api_key=api_key,
            temperature=0.4
        )
        self.llm_embeddings = OpenAIEmbeddings(openai_api_key=api_key)
        self.vectorstore: Optional[FAISS] = None

    @staticmethod
    def _preprocess_template_string(template: str) -> str:
        """Remove leading whitespace and indentation."""
        return textwrap.dedent(template)

    def set_job_description(self, job_description_text: str) -> None:
        """
        Process job description and initialize vectorstore for RAG-based extraction.
        
        Args:
            job_description_text: The full job description text
        """
        # Save to temporary file for TextLoader
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as temp_file:
            temp_file.write(job_description_text)
            temp_file_path = temp_file.name
        
        try:
            loader = TextLoader(temp_file_path, encoding="utf-8", autodetect_encoding=True)
            document = loader.load()
        except Exception as e:
            raise RuntimeError(f"Error loading job description: {e}")
        finally:
            os.remove(temp_file_path)
        
        # Split text into chunks for better retrieval
        text_splitter = TokenTextSplitter(chunk_size=500, chunk_overlap=50)
        all_splits = text_splitter.split_documents(document)
        
        # Create FAISS vectorstore
        try:
            self.vectorstore = FAISS.from_documents(documents=all_splits, embedding=self.llm_embeddings)
        except Exception as e:
            raise RuntimeError(f"Error creating vectorstore: {e}")

    def _retrieve_context(self, query: str, top_k: int = 3) -> str:
        """
        Retrieve the most relevant text fragments using the retriever.
        
        Args:
            query: The search query
            top_k: Number of fragments to retrieve
            
        Returns:
            str: Concatenated relevant text fragments
        """
        if not self.vectorstore:
            raise ValueError("Vectorstore not initialized. Call set_job_description() first.")
        
        retriever = self.vectorstore.as_retriever()
        retrieved_docs = retriever.get_relevant_documents(query)[:top_k]
        context = "\n\n".join(doc.page_content for doc in retrieved_docs)
        return context

    def _extract_information(self, question: str, retrieval_query: str) -> str:
        """
        Extract specific information using RAG (Retrieval Augmented Generation).
        
        Args:
            question: The question to ask the LLM
            retrieval_query: The query to use for retrieving relevant context
            
        Returns:
            str: The extracted information
        """
        context = self._retrieve_context(retrieval_query)
        
        template = self._preprocess_template_string("""
        You are an expert at extracting specific information from job descriptions.
        Carefully read the context below and provide a clear, concise answer to the question.
        If the information is not available, respond with "Not specified".
        
        Context:
        {context}
        
        Question: {question}
        
        Answer:
        """)
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            result = chain.invoke({"context": context, "question": question})
            return result.strip()
        except Exception as e:
            return f"Error: {e}"

    def extract_job_description(self) -> str:
        """Extract the full job description summary."""
        question = "What is the job description? Provide a comprehensive summary."
        retrieval_query = "Job description responsibilities requirements"
        return self._extract_information(question, retrieval_query)

    def extract_company_name(self) -> str:
        """Extract the company name."""
        question = "What is the company's name?"
        retrieval_query = "Company name"
        return self._extract_information(question, retrieval_query)

    def extract_role(self) -> str:
        """Extract the job role/title."""
        question = "What is the role or job title?"
        retrieval_query = "Job title role position"
        return self._extract_information(question, retrieval_query)

    def extract_location(self) -> str:
        """Extract the job location."""
        question = "What is the location mentioned in this job description?"
        retrieval_query = "Location office remote hybrid"
        return self._extract_information(question, retrieval_query)

    def extract_recruiter_email(self) -> str:
        """Extract the recruiter's email address."""
        question = "What is the recruiter's or contact email address?"
        retrieval_query = "Recruiter email contact"
        email = self._extract_information(question, retrieval_query)
        
        # Validate email using regex
        email_regex = r'[\w\.-]+@[\w\.-]+\.\w+'
        if re.match(email_regex, email):
            return email
        return "Not specified"

    def extract_salary_range(self) -> str:
        """Extract salary/compensation information."""
        question = "What is the salary range or compensation mentioned?"
        retrieval_query = "Salary compensation pay range"
        return self._extract_information(question, retrieval_query)

    def extract_required_skills(self) -> str:
        """Extract required skills and qualifications."""
        question = "What are the required skills and qualifications?"
        retrieval_query = "Required skills qualifications experience"
        return self._extract_information(question, retrieval_query)

    def extract_preferred_skills(self) -> str:
        """Extract preferred/nice-to-have skills."""
        question = "What are the preferred or nice-to-have skills?"
        retrieval_query = "Preferred skills nice to have bonus"
        return self._extract_information(question, retrieval_query)

    def extract_all_info(self) -> Dict[str, str]:
        """
        Extract all available information from the job description.
        
        Returns:
            dict: Dictionary containing all extracted information
        """
        return {
            "company": self.extract_company_name(),
            "role": self.extract_role(),
            "location": self.extract_location(),
            "description": self.extract_job_description(),
            "required_skills": self.extract_required_skills(),
            "preferred_skills": self.extract_preferred_skills(),
            "salary_range": self.extract_salary_range(),
            "recruiter_email": self.extract_recruiter_email(),
        }

    def parse_job_from_text(self, job_description_text: str) -> Dict[str, str]:
        """
        Convenience method to parse job description in one call.
        
        Args:
            job_description_text: Full job description text
            
        Returns:
            dict: Dictionary containing all extracted information
        """
        self.set_job_description(job_description_text)
        return self.extract_all_info()

