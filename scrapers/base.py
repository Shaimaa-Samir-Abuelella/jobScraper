from abc import ABC, abstractmethod

class BaseScraper(ABC):
    def __init__(self, proposal_service, telegram_client):
        self.proposal_service = proposal_service
        self.telegram = telegram_client

    @abstractmethod
    def scrape(self):
        ...

    def enrich_and_notify(self, jobs):
        for job in jobs:
            try:
                self.proposal_service.generate(job)
                msg = f"""🎯 <b>فرصة جديدة من خمسات</b>
    
    <b>العنوان:</b> {job.title}
    🔗 <a href="{job.url}">فتح الوظيفة</a>
    
    <b>ملخص:</b>
    <pre>{job.summary}</pre>
    
    <b>خطة العمل:</b>
    <pre>{job.plan}</pre>
    
    <b>البروبوزال:</b>
    <pre>{job.proposal}</pre>
    """


                self.telegram.send(msg)
            except Exception as e:
                print(e)
