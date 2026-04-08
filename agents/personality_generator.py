from typing import Dict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


class PersonalityGenerator:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
    
    def generate_personality_prompt(self, character_description: str) -> str:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个专业的角色性格设计师，擅长根据简短描述创建详细、生动的角色性格提示词。"),
            ("user", """请根据以下角色描述，生成一个详细的角色性格提示词，用于狼人杀游戏中的AI玩家。

角色描述：{character_description}

请生成包含以下内容的性格提示词：
1. 角色的基本性格特点（至少5个形容词）
2. 角色的说话风格和语气
3. 角色的思考方式和推理习惯
4. 角色在狼人杀游戏中可能的策略倾向
5. 角色的口头禅或常用表达

请用中文回答，格式清晰，大约300-500字。""")
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({"character_description": character_description})
        return response.content
    
    def create_player_personality(self, name: str, character_description: str) -> Dict[str, str]:
        personality_prompt = self.generate_personality_prompt(character_description)
        
        return {
            "name": name,
            "character_description": character_description,
            "personality_prompt": personality_prompt
        }
