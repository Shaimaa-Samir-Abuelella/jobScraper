class ProposalService:
    def __init__(self, llm_client):
        self.llm = llm_client

    def generate(self, job):
        prompt = self._build_prompt(job.title, job.description)
        data = self.llm.generate_json(prompt)
        job.plan = data.get("plan", "")
        job.proposal = data.get("proposal", "")
        job.summary = data.get("summary", "")
        return job

    def _build_prompt(self, title, description):
        if not description:
            description = "لا يوجد وصف"
        return f"""
You are an expert Arabic-speaking freelancer and project planner.

You will receive a job post (title + description) in Arabic from a freelancing website.

JOB TITLE (Arabic):
{title}

JOB DESCRIPTION (Arabic):
{description}

YOUR TASKS:
1) Read and deeply understand the Arabic job title and description.
2) Produce a short Arabic summary of the job (2–4 جمل) يوضح المطلوب من العميل بشكل بسيط وواضح.
3) Design a clear, step-by-step work plan IN ARABIC that explains exactly how I will execute this project from start to finish.
4) Write a professional PROPOSAL that is a mix of Arabic and English:
   - The main body and explanations should be in Arabic.
   - Use English for technical terms, tools, and short phrases when it makes sense (e.g. Python, web scraping, OCR, AI, prompts, APIs).
   - The proposal should sound natural for an Arabic-speaking client who is comfortable with some English tech terms.

WHAT TO INCLUDE:

A) "summary" (ARABIC):
   - 2–4 جمل تلخّص هدف المشروع، نوع المهمة، وأهم المتطلبات بشكل واضح ومباشر.

B) "plan" (ARABIC ONLY):
   - Detailed, numbered steps explaining how I will do the task.
   - Mention tools, libraries, and technologies (Python, web scraping, OCR, AI models, etc.) but keep the explanation itself in Arabic.
   - Explain the workflow so the project to help the task developer.
   - Use lists to show your answer.
   - Make your answer confine and precise.

C) "proposal" (MIX ARABIC(Make most of the response in Arabic) + ENGLISH(use it only for technical abbreviations)):
   - Start with a tailored opening in Arabic يثبت أنك فهمت احتياج العميل.
   - Mention my experience في الذكاء الاصطناعي، OCR، Python، Web Scraping، وتحليل البيانات فقط عندما يكون ذلك مناسبًا لهذا المشروع.
   - Briefly outline the steps (يمكن خلط العربي مع English في الأجزاء التقنية).
   - Mention estimated timeline and deliverables clearly.
   - Use a confident, polite tone.
   - Avoid unrealistic promises.
   - Do NOT mention that you are an AI or language model.
   - Do NOT use placeholders مثل [اسم العميل] أو [ضع هنا كذا].
   - Make you answer confine and precise.

OUTPUT FORMAT (VERY IMPORTANT):
Return ONLY valid JSON. No comments, no markdown, no explanations.

Exact format:

{{
  "summary": "ملخص عربي قصير لوصف الوظيفة هنا...",
  "plan": "نص خطة العمل التفصيلية بالعربية هنا...",
  "proposal": "نص العرض (البروبوزال) المزيج عربي + إنجليزي هنا..."
}}
""".strip()

