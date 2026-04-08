import re
from typing import List, Dict, Any, Optional, Tuple
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from core.game_state import GameState, Player, GamePhase
from core.roles import RoleType, Camp
from agents.memory_manager import MemoryManager
from pydantic import BaseModel, Field


class ReasoningEngine:
    def __init__(self, llm: ChatOpenAI, player: Player, game_state: GameState):
        self.llm = llm
        self.player = player
        self.game_state = game_state
        self.memory_manager = MemoryManager(player)
    
    def get_system_prompt(self) -> str:
        role_info = f"""你是狼人杀游戏中的玩家，你的名字是：{self.player.name}
你的角色是：{self.player.role.name}
你的阵营是：{self.player.camp.value}
你的角色描述：{self.player.role.description}
你的能力：{', '.join(self.player.role.abilities)}

你的性格设定：
{self.player.personality_prompt}

【狼人杀游戏规则详解】

一、游戏简介
狼人杀是一款多人参与的逻辑推理类桌面游戏。玩家被分为两个阵营：狼人阵营和村民阵营。村民阵营需要在白天通过投票驱逐狼人，而狼人阵营则需要在夜晚杀死所有村民。

二、角色介绍
（一）村民阵营角色
1. 预言家（Prophet）- 每晚可以查验一名玩家的身份，可以得知该玩家是狼人还是好人
2. 女巫（Witch）- 拥有一瓶解药和一瓶毒药。解药可以救活当晚被狼人杀死的人，毒药可以毒死任意一名玩家
3. 猎人（Hunter）- 当猎人死亡时，可以选择带走一名存活的玩家。但如果被女巫毒死，则无法使用技能
4. 白痴（Idiot）- 白痴被投票出局时，不会死亡，而是翻开身份牌并存活，但失去投票权和发言权
5. 守卫（Guardian）- 每晚可以守护一名玩家免受狼人袭击，但不能连续两晚守护同一名玩家
6. 普通村民 - 没有特殊能力，靠分析发言找出狼人

（二）狼人阵营角色
1. 狼人（Werewolf）- 每晚可以杀死一名玩家
2. 白狼王等特殊狼人 - 有特殊能力

三、游戏流程
（一）夜晚阶段
1. 狼人睁眼：狼人之间互相确认，然后选择杀死一名玩家
2. 预言家睁眼：选择一名玩家进行查验
3. 女巫睁眼：主持人告知女巫今晚狼人杀死的玩家，女巫选择是否使用解药或毒药
4. 守卫睁眼：选择一名玩家进行守护

（二）白天阶段
1. 主持人宣布天亮
2. 公布昨晚死亡信息（如无死亡则宣布平安夜）
3. 存活玩家按顺序发言讨论
4. 主持人宣布投票
5. 得票最多的玩家被驱逐出局
6. 进入下一个夜晚

四、胜负判定
好人阵营胜利条件：所有狼人被驱逐出局
狼人阵营胜利条件：所有村民被杀死，或狼人数量等于好人数量

五、常用术语
- 金水：预言家验过的好人
- 银水：女巫用解药救过的人
- 查杀：预言家验过的狼人
- 悍跳：狼人假装预言家
- 踩：发言中质疑某玩家
- 自爆：狼人主动表明身份并出局

六、游戏技巧
（一）好人阵营
1. 预言家应尽早跳明身份，报查验结果
2. 女巫应合理使用解药和毒药，优先救人
3. 村民应认真分析发言，找出狼人
4. 注意观察玩家的发言顺序和心态变化

（二）狼人阵营
1. 悍跳预言家时应保持冷静，逻辑清晰
2. 狼队应统一目标，避免自乱阵脚
3. 适当做低身份玩家的好人面
4. 关键时刻可以自爆保狼队

你的目标是帮助自己的阵营获胜！
发言要符合你的性格设定！
请根据你的角色和性格，自然地参与游戏。"""
        return role_info
    
    def analyze_game_state(self) -> Dict[str, Any]:
        alive_players = self.game_state.get_alive_players()
        werewolves = self.game_state.get_werewolves()
        villagers = self.game_state.get_villagers()
        
        analysis = {
            "alive_count": len(alive_players),
            "werewolf_count": len(werewolves),
            "villager_count": len(villagers),
            "my_status": self.player.status.value,
            "phase": self.game_state.phase.value,
            "day": self.game_state.day_count,
            "night": self.game_state.night_count,
        }
        return analysis
    
    def _parse_action_response(self, response: str) -> Tuple[Optional[str], Optional[int]]:
        """解析包含思考和行动的响应"""
        thinking = None
        action = None
        
        lines = response.strip().split('\n')
        thinking_lines = []
        action_part_found = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if action_part_found:
                try:
                    num = int(line)
                    action = num
                    break
                except ValueError:
                    pass
            
            if line.startswith('【思考】') or line.startswith('[思考]'):
                continue
            if line.startswith('【行动】') or line.startswith('[行动]') or line.startswith('【选择】') or line.startswith('[选择]') or line.startswith('【投票】') or line.startswith('[投票]'):
                action_part_found = True
                content = line.split('】', 1)[-1] if '】' in line else line.split(']', 1)[-1]
                content = content.strip()
                if content:
                    try:
                        action = int(content)
                    except ValueError:
                        pass
                continue
            
            if not action_part_found:
                thinking_lines.append(line)
        
        if thinking_lines:
            thinking = '\n'.join(thinking_lines)
        
        if action is None:
            for line in lines:
                line = line.strip()
                matches = re.findall(r'\d+', line)
                if matches:
                    for match in matches:
                        try:
                            num = int(match)
                            if num > 0:
                                action = num
                                break
                        except ValueError:
                            pass
                if action is not None:
                    break
        
        return thinking, action
    
    def generate_speech(self, context: str, show_thinking: bool = False) -> Tuple[str, Optional[str]]:
        memories = self.memory_manager.format_memories_for_prompt()
        game_analysis = self.analyze_game_state()
        
        if show_thinking:
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.get_system_prompt()),
                ("user", """当前游戏状态：
{game_analysis}

你的记忆：
{memories}

当前情境：
{context}

请先进行思考，然后发表你的言论。

⚠️ 重要要求：
1. 你的【思考】中应该说明你打算怎么说
2. 你的【发言】必须和【思考】中的打算一致！

【输出格式要求】
输出必须严格遵循以下JSON结构：
    {{
        "thinking": "字符串类型，必需字段，你的思考内容，200-300字",
        "speech": "字符串类型，必需字段，你的发言内容，100-300字，必须和思考一致"
    }}

请严格按照格式和要求输出。""")
            ])

            class Speech(BaseModel):
                """白天阶段的发言"""
                thinking: str = Field(description="你的思考内容")
                speech: str = Field(description="你的发言内容")

            llm_with_structure = self.llm.with_structured_output(Speech)
            
            chain = prompt | llm_with_structure
            response = chain.invoke({
                "game_analysis": str(game_analysis),
                "memories": memories,
                "context": context
            })

            thinking = response.thinking
            speech = response.speech
            
            if speech:
                self.memory_manager.record_observation(f"我发言：{speech}", 6)
            return speech, thinking
        else:
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.get_system_prompt()),
                ("user", """当前游戏状态：
{game_analysis}

你的记忆：
{memories}

当前情境：
{context}

请根据你的角色、性格和当前情况，发表你的言论。发言要自然，符合你的性格特点，长度适中（100-300字）。
直接输出你的发言内容，不要有其他说明。""")
            ])
            
            chain = prompt | self.llm
            response = chain.invoke({
                "game_analysis": str(game_analysis),
                "memories": memories,
                "context": context
            })
            
            speech = response.content
            self.memory_manager.record_observation(f"我发言：{speech}", 6)
            return speech, None
    
    def choose_vote_target(self, candidates: List[int], show_thinking: bool = False) -> Tuple[int, Optional[str]]:
        memories = self.memory_manager.format_memories_for_prompt()
        
        candidate_names = [self.game_state.get_player(pid).name for pid in candidates]
        candidate_list = str(list(zip(candidates, candidate_names)))
        candidate_map = {self.game_state.get_player(pid).name: pid for pid in candidates}
        
        if show_thinking:
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.get_system_prompt()),
                ("user", """你的记忆：
{memories}

可投票的玩家：{candidates}

请先进行思考，然后选择一个你最想投票驱逐的玩家。

⚠️ 重要要求：
1. 你的【思考】中必须明确说明你想选谁（要说玩家名字）
2. 你的【选择】必须和【思考】中决定的人选完全一致！
3. 绝对不能出现思考说选A，但选择写B的情况！

【输出格式要求】
输出必须严格遵循以下JSON结构：
    {{
        "thinking": "字符串类型，必需字段，你的思考内容，200-300字，必须明确说出要选谁的名字或不行动",
        "chosen_id": "整数类型，必需字段，你选择的玩家ID，只写数字；如果不行动，写-1；必须和思考一致"
    }}

请严格按照格式和要求输出。""")
            ])

            class Choice(BaseModel):
                thinking: str = Field(description="你的思考内容")
                chosen_id: int = Field(description="你选择的玩家ID")

            llm_with_structure = self.llm.with_structured_output(Choice)

            chain = prompt | llm_with_structure
            response = chain.invoke({
                "memories": memories,
                "candidates": candidate_list
            })

            thinking, chosen_id = response.thinking, response.chosen_id
            
            if chosen_id is None or chosen_id not in candidates:
                if thinking:
                    for name, pid in candidate_map.items():
                        if name in thinking:
                            chosen_id = pid
                            break
            
            if chosen_id is not None and chosen_id in candidates:
                self.memory_manager.record_strategy(f"决定投票给玩家{chosen_id}")
                return chosen_id, thinking
            else:
                return candidates[0], thinking
        else:
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.get_system_prompt()),
                ("user", """你的记忆：
{memories}

可投票的玩家：{candidates}

请根据你的分析，选择一个你最想投票驱逐的玩家。
只返回该玩家的ID（数字），不要其他内容。""")
            ])
            
            chain = prompt | self.llm
            response = chain.invoke({
                "memories": memories,
                "candidates": candidate_list
            })
            
            try:
                chosen_id = int(response.content.strip())
                if chosen_id in candidates:
                    self.memory_manager.record_strategy(f"决定投票给玩家{chosen_id}")
                    return chosen_id, None
            except ValueError:
                pass
            
            return candidates[0], None
    
    def choose_night_action(self, action_type: str, available_targets: List[int], show_thinking: bool = False) -> Tuple[Optional[int], Optional[str]]:
        memories = self.memory_manager.format_memories_for_prompt()
        
        target_name_pairs = []
        target_map = {}
        for pid in available_targets:
            if pid == -1:
                target_name_pairs.append((-1, "不行动"))
            else:
                player = self.game_state.get_player(pid)
                if player:
                    target_name_pairs.append((pid, player.name))
                    target_map[player.name] = pid
        
        action_descriptions = {
            "werewolf_kill": "作为狼人，请选择一个要杀死的玩家",
            "prophet_check": "作为预言家，请选择一个要查验的玩家",
            "witch_heal": "作为女巫，是否使用解药救人？如果是，选择目标；如果不行动，选择-1",
            "witch_poison": "作为女巫，是否使用毒药？如果是，选择目标；如果不行动，选择-1",
            "guardian_protect": "作为守卫，请选择一个要守护的玩家",
            "cupid_choose": "作为丘比特，请选择第一个情侣",
        }
        
        target_list = str(target_name_pairs)
        
        if show_thinking:
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.get_system_prompt()),
                ("user", """你的记忆：
{memories}

可用目标：{targets}

{action_description}

⚠️ 重要要求：
1. 你的【思考】中必须明确说明你想选谁或是否行动（要说玩家名字）
2. 你的【选择】必须和【思考】中决定的完全一致！
3. 绝对不能出现思考说选A，但选择写B的情况！

【输出格式要求】
输出必须严格遵循以下JSON结构：
{{
  "thinking": "字符串类型，必需字段，你的思考内容，200-300字，必须明确说出要选谁的名字或不行动",
  "chosen_id": "整数类型，必需字段，你选择的玩家ID，只写数字；如果不行动，写-1；必须和思考一致"
}}

请严格按照格式和要求输出。""")
            ])

            class Choice(BaseModel):
                thinking: str = Field(description="你的思考内容")
                chosen_id: int = Field(description="你选择的玩家ID")

            llm_with_structure = self.llm.with_structured_output(Choice)

            chain = prompt | llm_with_structure
            response = chain.invoke({
                "memories": memories,
                "targets": target_list,
                "action_description": action_descriptions.get(action_type, "请做出选择")
            })

            thinking, chosen_id = response.thinking, response.chosen_id
            
            if chosen_id is None or (chosen_id != -1 and chosen_id not in available_targets):
                if thinking:
                    for name, pid in target_map.items():
                        if name in thinking:
                            chosen_id = pid
                            break
            
            if chosen_id is not None:
                if chosen_id == -1:
                    return None, thinking
                if chosen_id in available_targets:
                    return chosen_id, thinking
            
            valid_targets = [pid for pid in available_targets if pid != -1]
            return valid_targets[0] if valid_targets else None, thinking
        else:
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.get_system_prompt()),
                ("user", """你的记忆：
{memories}

可用目标：{targets}

{action_description}

请做出你的选择，只返回玩家ID（数字），如果不行动则返回-1。""")
            ])
            
            chain = prompt | self.llm
            response = chain.invoke({
                "memories": memories,
                "targets": target_list,
                "action_description": action_descriptions.get(action_type, "请做出选择")
            })
            
            try:
                chosen_id = int(response.content.strip())
                if chosen_id == -1:
                    return None, None
                if chosen_id in available_targets:
                    return chosen_id, None
            except ValueError:
                pass
            
            valid_targets = [pid for pid in available_targets if pid != -1]
            return valid_targets[0] if valid_targets else None, None
    
    def generate_werewolf_discussion(self, context: str, discussion_history: str = "") -> str:
        """生成狼人讨论发言"""
        memories = self.memory_manager.format_memories_for_prompt()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.get_system_prompt()),
            ("user", """你的记忆：
{memories}

当前情境：
{context}

讨论历史：
{discussion_history}

作为狼人，请和你的狼队友讨论今晚要杀死谁。
发言要符合你的性格特点，长度适中（50-150字）。
直接输出你的讨论内容，不要有其他说明。""")
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({
            "memories": memories,
            "context": context,
            "discussion_history": discussion_history if discussion_history else "（刚开始讨论）"
        })
        
        discussion = response.content
        self.memory_manager.record_observation(f"我在狼队讨论中说：{discussion}", 7)
        return discussion
    
    def process_public_message(self, speaker_id: int, message: str) -> None:
        speaker = self.game_state.get_player(speaker_id)
        if speaker:
            self.memory_manager.record_observation(
                f"{speaker.name}说：{message}",
                importance=6
            )
    
    def should_self_divulge(self) -> bool:
        if self.player.role_type == RoleType.PROPHET and self.game_state.day_count >= 1:
            return True
        return False
