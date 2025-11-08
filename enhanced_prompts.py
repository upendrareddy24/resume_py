"""
Enhanced Resume Generation Prompts
Focuses on 2-page format, 10 bullet professional summary, and most recent relevant experience
"""

ENHANCED_RESUME_PROMPT = """
You are an expert resume writer creating a tailored, ATS-optimized resume for a specific job application.

**Job Details:**
Company: {company_name}
Position: {job_title}
Job Description: {job_description}

**Candidate's Background:**
{resume_text}

**Requirements:**
1. Create a 2-PAGE professional resume tailored for this specific role
2. Start with a PROFESSIONAL SUMMARY section with EXACTLY 10 bullet points highlighting:
   - Most relevant skills and expertise for THIS specific role
   - Quantifiable achievements that match the job requirements
   - Technical proficiencies mentioned in the job description
   - Leadership and collaboration abilities
   - Domain expertise relevant to the company/industry
   
3. WORK EXPERIENCE section:
   - Prioritize the MOST RECENT and MOST RELEVANT experience for this role
   - Include 2-3 most recent positions that align with the job requirements
   - For each position, provide 4-6 impactful bullet points that:
     * Use strong action verbs (Led, Architected, Implemented, Optimized, etc.)
     * Include quantifiable results (%, $, time saved, users impacted, etc.)
     * Highlight technologies and skills mentioned in the job description
     * Demonstrate progression and increasing responsibility
   - If older experience is highly relevant, include 1-2 additional positions with fewer bullets

4. TECHNICAL SKILLS section:
   - Organize by category (Languages, Frameworks, Cloud/DevOps, Databases, etc.)
   - Prioritize skills mentioned in the job description
   - Include proficiency levels if relevant

5. EDUCATION section:
   - Degree, institution, graduation year
   - GPA if >3.5
   - Relevant coursework if early career

6. Optional sections (if space allows and relevant):
   - KEY PROJECTS: 2-3 impressive projects with measurable outcomes
   - CERTIFICATIONS: Industry-recognized certifications
   - PUBLICATIONS/PATENTS: If in research/technical role

**Formatting Guidelines:**
- Use clean, professional formatting
- Keep consistent tense (past tense for previous roles, present for current)
- No personal pronouns
- Focus on achievements, not just responsibilities
- Tailor language to match the company's culture and values
- Ensure content fits naturally into 2 pages

**Output Format:**
Provide the complete resume as formatted text, ready to be converted to PDF.
Use clear section headers (all caps, e.g., "PROFESSIONAL SUMMARY", "WORK EXPERIENCE").
Separate sections with blank lines.

Begin the resume with the candidate's name and contact information, then proceed with the sections as outlined.
"""

ENHANCED_COVER_LETTER_PROMPT = """
You are an expert cover letter writer creating a compelling, personalized cover letter for a specific job application.

**Job Details:**
Company: {company_name}
Position: {job_title}
Job Description: {job_description}

**Candidate's Background:**
{resume_text}

**Requirements:**
1. Create a 1-PAGE cover letter that:
   - Opens with a compelling hook that shows genuine interest in the company and role
   - Demonstrates understanding of the company's mission, products, or recent news
   - Highlights 3-4 most relevant achievements that directly address the job requirements
   - Provides specific examples with quantifiable results
   - Shows cultural fit and alignment with company values
   - Closes with a confident call to action

2. Structure:
   - Opening paragraph: Hook + Why this company + Why this role
   - Body paragraphs (2-3): Relevant achievements and skills
   - Closing paragraph: Value proposition + Next steps

3. Tone:
   - Professional yet personable
   - Confident without being arrogant
   - Enthusiastic about the opportunity
   - Match the company's communication style (formal for enterprise, casual for startups)

4. Content Guidelines:
   - Don't repeat the resume - provide context and stories
   - Use the STAR method (Situation, Task, Action, Result) for examples
   - Connect your experience directly to their needs
   - Show, don't tell (use specific examples, not generic claims)
   - Keep it concise - aim for 3-4 paragraphs total

**Output Format:**
Provide the complete cover letter as formatted text, ready to be converted to PDF.
Do NOT include the date, address, or "To Whom It May Concern" - these will be added automatically.
Start with "Dear Hiring Manager," or "Dear [Company] Team,"
End with "Sincerely," (closing signature will be added automatically).
"""

PROFESSIONAL_SUMMARY_PROMPT = """
Generate a compelling professional summary with EXACTLY 10 bullet points for a {job_title} position at {company_name}.

**Job Description:**
{job_description}

**Candidate Background:**
{resume_text}

**Instructions:**
Create 10 impactful bullet points that:
1. Highlight the most relevant skills and experience for THIS specific role
2. Include quantifiable achievements (%, $, scale, impact)
3. Mention key technologies/skills from the job description
4. Show progression and leadership
5. Demonstrate domain expertise
6. Are action-oriented and results-focused
7. Are concise (1-2 lines each)
8. Use strong verbs (Led, Architected, Scaled, Optimized, etc.)
9. Show both technical depth and business impact
10. Create a compelling narrative of the candidate's value

**Format:**
Return ONLY the 10 bullet points, one per line, starting with "•"
Do NOT include a header or section title.
Do NOT include any other text.

Example format:
• Led cross-functional team of 12 engineers to deliver cloud migration, reducing infrastructure costs by 40% ($2M annually)
• Architected and implemented microservices platform serving 50M+ daily active users with 99.99% uptime
...
"""

WORK_EXPERIENCE_PROMPT = """
Generate a tailored work experience section focusing on the MOST RECENT and MOST RELEVANT positions for a {job_title} role at {company_name}.

**Job Description:**
{job_description}

**Candidate's Work History:**
{experience_text}

**Instructions:**
1. Select the 2-3 most recent and relevant positions
2. For each position, provide:
   - Position Title | Company Name
   - Employment Period | Location
   - 4-6 impactful bullet points that:
     * Align with the job requirements
     * Include quantifiable results
     * Highlight relevant technologies and skills
     * Show increasing responsibility and impact
     * Use strong action verbs

3. If the candidate has older but highly relevant experience, include 1 additional position with 3-4 bullets

**Prioritization Criteria:**
- Relevance to target role: 50%
- Recency: 30%
- Impact and achievements: 20%

**Format:**
Position Title | Company Name
Month Year - Month Year | Location
• Achievement/responsibility with quantifiable impact
• Achievement/responsibility with quantifiable impact
...

[Repeat for each position]
"""

