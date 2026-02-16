from dataclasses import dataclass

@dataclass
class Job:
    title: str
    url: str
    description: str = ""
    plan: str = ""
    proposal: str = ""
