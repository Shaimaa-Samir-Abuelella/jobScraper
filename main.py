from config import AppConfig
from clients.llm_client import LLMClient
from clients.telegram_client import TelegramClient
from services.proposal_service import ProposalService
from scrapers.khamsat import KhamsatScraper
from scrapers.mostaql import MostaqlScraper

def main():
    cfg=AppConfig()
    llm=LLMClient(cfg.llm_api_base,cfg.llm_api_key,cfg.llm_model)
    telegram=TelegramClient(cfg.telegram_token,cfg.telegram_chat_id)
    service=ProposalService(llm)

    for cls in (KhamsatScraper,MostaqlScraper):
        scraper=cls(service,telegram)
        jobs=scraper.scrape()
        scraper.enrich_and_notify(jobs)

if __name__=="__main__":
    main()
