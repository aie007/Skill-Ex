import re
from typing import List
from backend.core.interfaces import ISkillExtractor
from backend.config.settings import settings

class RegexSkillExtractor(ISkillExtractor):
    def __init__(self, skill_list: List[str] = None):
        self.skill_list = skill_list or settings.skills
        # Escape symbols like C++ and join with word boundaries
        pattern_string = r'\b(' + '|'.join(map(re.escape, self.skill_list)) + r')\b'
        self.pattern = re.compile(pattern_string, re.IGNORECASE)

    def extract(self, text: str) -> List[str]:
        if not text: return []
        matches = self.pattern.findall(text)
        # Normalize casing based on the original list
        return list(set(next((s for s in self.skill_list if s.lower() == m.lower()), m) for m in matches))

class ExperienceExtractor:
    def __init__(self, levels_config: dict = None):
        self.levels = levels_config or settings.experience_levels
        # Pattern to find years of experience (e.g., "5+ years", "3-5 years")
        self.years_pattern = re.compile(r'(\d+)\s*(?:\+|-|\sto\s)?\s*\d*\s*years?', re.IGNORECASE)

    def extract(self, title: str, description: str) -> str:
        # 1. Check title for explicit seniority keywords
        for level, pattern in self.levels.items():
            if re.search(pattern, title, re.IGNORECASE):
                return level.capitalize()

        # 2. Check description for years of experience
        match = self.years_pattern.search(description)
        if match:
            years = int(match.group(1))
            if years < 2: return "Junior"
            if 2 <= years <= 5: return "Mid"
            return "Senior"
        
        return "Not Specified"
