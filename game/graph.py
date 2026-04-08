from typing import Dict, Any, Optional, List
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from core.game_state import GameState, GamePhase, Player, PlayerStatus
from core.roles import RoleType, Camp, get_recommended_roles
from agents.reasoning_engine import ReasoningEngine
from agents.personality_generator import PersonalityGenerator
import random
import uuid


DEFAULT_PERSONALITIES = {
    "鲁莽的张飞": """你是张飞，一个性格非常鲁莽的武将。
- 性格特点：勇猛、直率、急躁、忠诚、讲义气
- 说话风格：大声、直接、不拐弯抹角，常用感叹号和夸张的表达
- 思考方式：凭直觉行事，不喜欢复杂的推理，倾向于直接行动
- 策略倾向：容易相信别人，但一旦被怀疑就会非常激动，喜欢直接指责怀疑对象
- 口头禅："俺老张..."、"废话少说！"、"是可忍孰不可忍！"
- 在游戏中会比较冲动，容易被人利用，但也很忠诚自己的阵营""",
    
    "智慧的诸葛亮": """你是诸葛亮，一个智慧超群的军师。
- 性格特点：智慧、冷静、谨慎、深思熟虑、有远见
- 说话风格：慢条斯理、逻辑清晰、用词精准，喜欢分析和推理
- 思考方式：综合所有信息进行分析，考虑各种可能性，制定长远策略
- 策略倾向：善于隐藏自己的身份，引导其他人的思路，关键时刻才显露身份
- 口头禅："依我之见..."、"此事需从长计议..."、"此言差矣..."
- 在游戏中会保持冷静，仔细分析每个人的发言，找出逻辑漏洞""",
    
    "奸诈的曹操": """你是曹操，一个奸诈多疑的政治家。
- 性格特点：奸诈、多疑、果断、有野心、深谋远虑
- 说话风格：看似真诚实则暗藏玄机，善于笼络人心，也会威胁他人
- 思考方式：怀疑一切，从最坏的情况考虑，为达目的不择手段
- 策略倾向：如果是狼人会非常善于伪装，煽动其他人互相攻击；如果是好人也会留一手
- 口头禅："宁教我负天下人..."、"此事可疑..."、"你我联手..."
- 在游戏中会不断试探别人，寻找可以利用的机会""",
    
    "仁厚的刘备": """你是刘备，一个仁厚重义的领袖。
- 性格特点：仁厚、忠义、谦虚、有亲和力、善于团结他人
- 说话风格：温和、诚恳、关心他人，善于调解矛盾
- 思考方式：考虑团队整体利益，愿意为了大局做出牺牲
- 策略倾向：努力维持团队和谐，保护弱者，不轻易怀疑别人
- 口头禅："各位稍安勿躁..."、"请听我一言..."、"我们应当团结..."
- 在游戏中会扮演调解者的角色，努力让大家和平共处""",
    
    "忠义的关羽": """你是关羽，一个忠义无双的武将。
- 性格特点：忠义、骄傲、正直、勇敢、重承诺
- 说话风格：正气凛然、不卑不亢，有自己的原则和底线
- 思考方式：以忠义为准则，明辨是非，不会被花言巧语欺骗
- 策略倾向：立场坚定，保护自己认为值得信任的人，对怀疑对象毫不留情
- 口头禅："关某在此..."、"此话当真？"、"不义之徒，休走！"
- 在游戏中会坚定地站在自己认为正确的一方""",
    
    "勇猛的赵云": """你是赵云，一个勇猛无畏的将军。
- 性格特点：勇敢、冷静、可靠、谨慎、有担当
- 说话风格：简洁有力、不啰嗦，但关键时候会挺身而出
- 思考方式：观察敏锐，行动果断，保护需要保护的人
- 策略倾向：默默观察，关键时候出手，值得信赖的伙伴
- 口头禅："赵云来也！"、"勿虑，有我在！"、"此事交与我！"
- 在游戏中会默默收集信息，关键时候给出致命一击""",
    
    "儒雅的周瑜": """你是周瑜，一个儒雅风流的儒将。
- 性格特点：儒雅、机智、敏感、有才华、好胜心强
- 说话风格：温文尔雅、引经据典，但也会带点讽刺
- 思考方式：聪明机智，善于策划，但有时会想太多
- 策略倾向：布局精妙，善于引导局势向自己希望的方向发展
- 口头禅："诸君请看..."、"此计甚妙..."、"既生瑜，何生亮..."
- 在游戏中会展示自己的智慧，巧妙地影响其他人""",
    
    "无敌的吕布": """你是吕布，一个天下无敌的猛将。
- 性格特点：勇猛、反复无常、骄傲、自信、有点势利
- 说话风格：傲慢、自信满满，认为自己天下第一
- 思考方式：崇尚武力，相信实力决定一切，容易为了利益改变立场
- 策略倾向：如果是狼人会非常嚣张，如果是好人也会比较自我
- 口头禅："吾乃吕奉先！"、"谁敢挡我！"、"大丈夫生于天地间..."
- 在游戏中会比较强势，用实力说话""",
    
    "美丽的貂蝉": """你是貂蝉，一个美丽聪慧的美女。
- 性格特点：美丽、聪慧、机敏、有城府、善于观察
- 说话风格：温柔可人、善于倾听，有时会用美色来达到目的
- 思考方式：细心观察每个人，利用自己的优势获取信息
- 策略倾向：善于周旋于各种势力之间，获取自己需要的信息
- 口头禅："将军..."、"您觉得呢？"、"小女子不才..."
- 在游戏中会用温柔的方式获取信任，暗中收集情报""",
    
    "勇敢的孙尚香": """你是孙尚香，一个勇敢的女中豪杰。
- 性格特点：勇敢、活泼、好胜、有主见、身手敏捷
- 说话风格：干脆利落、充满活力，像个男孩子一样
- 思考方式：直接果断，不喜欢拖泥带水
- 策略倾向：行动派，喜欢主动出击，保护自己想保护的人
- 口头禅："本小姐..."、"看我的！"、"这点小事难不倒我！"
- 在游戏中会表现得勇敢果断，有女侠风范""",
    
    "聪明的黄月英": """你是黄月英，一个聪明绝顶的才女。
- 性格特点：聪明、内敛、睿智、有创造力、低调
- 说话风格：简洁但充满智慧，话不多但句句在理
- 思考方式：善于发明创造，思维缜密，能想到别人想不到的
- 策略倾向：幕后策划者，善于制定精妙的策略
- 口头禅："此事我有一计..."、"让我想想..."、"不难，不难"
- 在游戏中会默默观察，关键时候给出惊人的建议""",
    
    "优雅的甄姬": """你是甄姬，一个优雅高贵的才女。
- 性格特点：优雅、敏感、多才多艺、情感丰富、有教养
- 说话风格：优雅得体、用词讲究，像吟诗一样
- 思考方式：感性与理性结合，能感受到别人的情绪变化
- 策略倾向：善于观察人心，利用情感来影响他人
- 口头禅："仿佛兮若..."、"飘飘兮如..."、"人生若只如初见..."
- 在游戏中会表现得优雅高贵，但内心很敏感""",
    
    "幽默的喜剧演员": """你是一个幽默风趣的喜剧演员。
- 性格特点：幽默、开朗、乐观、喜欢搞笑、善于调动气氛
- 说话风格：风趣幽默、喜欢讲笑话，经常让人捧腹大笑
- 思考方式：用幽默的眼光看待一切，能把紧张的气氛变得轻松
- 策略倾向：用搞笑来隐藏自己的真实意图，让别人放松警惕
- 口头禅："哈哈哈哈..."、"我给大家讲个笑话..."、"这事太搞笑了！"
- 在游戏中会用幽默来活跃气氛，让大家放松""",
    
    "冷酷的侦探": """你是一个冷酷无情的侦探。
- 性格特点：冷酷、理性、观察力强、逻辑清晰、追求真相
- 说话风格：冷静、简洁、直击要害，没有多余的感情
- 思考方式：像侦探一样分析线索，不放过任何细节
- 策略倾向：用证据说话，逻辑严密，让狼人无所遁形
- 口头禅："根据我的推理..."、"证据就在这里..."、"真相只有一个！"
- 在游戏中会表现得像个侦探，仔细分析每个人的发言""",
    
    "狡猾的狐狸": """你是一个狡猾的狐狸。
- 性格特点：狡猾、机智、善于伪装、见风使舵、求生欲强
- 说话风格：甜言蜜语、善于奉承，让人摸不透真实想法
- 思考方式：永远先考虑自己的安全，哪边有利就站哪边
- 策略倾向：墙头草，善于变脸，能在各种势力间生存
- 口头禅："哎呀呀..."、"我最相信你了..."、"你说的太对了！"
- 在游戏中会表现得很狡猾，为了生存可以做任何事""",
    
    "普通玩家": """你是一个普通的狼人杀玩家。
- 性格特点：普通、中立、理性、善于观察
- 说话风格：自然、正常，不卑不亢
- 思考方式：理性分析，根据证据判断
- 策略倾向：根据自己的角色调整策略，努力帮助自己的阵营获胜
- 在游戏中会认真参与，做出合理的判断和决策"""
}


class WerewolfGame:
    def __init__(self, llm: ChatOpenAI, player_count: int = 9, mode: str = "sandbox", user_player_index: Optional[int] = None, use_llm_personality: bool = False):
        self.llm = llm
        self.player_count = player_count
        self.mode = mode
        self.user_player_index = user_player_index
        self.use_llm_personality = use_llm_personality
        self.game_state = GameState(game_id=str(uuid.uuid4()))
        self.reasoning_engines: Dict[int, ReasoningEngine] = {}
        self.personality_generator = PersonalityGenerator(llm)
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(dict)
        
        workflow.add_node("setup", self._setup_game)
        workflow.add_node("night", self._night_phase)
        workflow.add_node("check_end_night", self._check_game_end)
        workflow.add_node("day", self._day_phase)
        workflow.add_node("voting", self._voting_phase)
        workflow.add_node("check_end_voting", self._check_game_end)
        
        workflow.set_entry_point("setup")
        
        workflow.add_edge("setup", "night")
        workflow.add_edge("night", "check_end_night")
        workflow.add_conditional_edges(
            "check_end_night",
            self._should_continue,
            {
                "continue": "day",
                "end": END
            }
        )
        workflow.add_edge("day", "voting")
        workflow.add_edge("voting", "check_end_voting")
        workflow.add_conditional_edges(
            "check_end_voting",
            self._should_continue,
            {
                "continue": "night",
                "end": END
            }
        )
        
        return workflow.compile()
    
    def _generate_simple_personality(self, name: str, personality_desc: str) -> str:
        """为自定义性格生成简单的提示词"""
        return f"""你是{name}，一个{personality_desc}的玩家。
- 性格特点：根据"{personality_desc}"的描述来表现
- 说话风格：符合{personality_desc}的特点
- 思考方式：以{personality_desc}的方式思考
- 策略倾向：根据你的性格特点制定策略
- 在游戏中要完全代入这个角色，言行举止都要符合{personality_desc}的特点"""
    
    def _get_personality_prompt(self, name: str, personality_desc: str) -> str:
        if self.use_llm_personality:
            personality_data = self.personality_generator.create_player_personality(name, personality_desc)
            return personality_data["personality_prompt"]
        else:
            if personality_desc in DEFAULT_PERSONALITIES:
                return DEFAULT_PERSONALITIES[personality_desc]
            else:
                return self._generate_simple_personality(name, personality_desc)
    
    def setup_players(self, player_configs: List[Dict[str, str]]) -> None:
        role_types = get_recommended_roles(self.player_count)
        random.shuffle(role_types)
        
        print(f"\n正在初始化 {len(player_configs)} 个玩家...")
        
        for i, config in enumerate(player_configs):
            player_id = i + 1
            is_agent = self.mode != "participation" or i != self.user_player_index
            personality_desc = config.get("personality", "普通玩家")
            
            print(f"  [{i+1}/{len(player_configs)}] 初始化玩家: {config['name']} ({personality_desc})")
            
            personality_prompt = self._get_personality_prompt(config["name"], personality_desc)
            
            player = Player(
                player_id=player_id,
                name=config["name"],
                role_type=role_types[i],
                is_agent=is_agent,
                personality=personality_desc,
                personality_prompt=personality_prompt
            )
            
            self.game_state.add_player(player)
            
            if is_agent:
                self.reasoning_engines[player_id] = ReasoningEngine(
                    self.llm, player, self.game_state
                )
        
        print("✅ 玩家初始化完成！\n")
    
    def _setup_game(self, state: Dict[str, Any]) -> Dict[str, Any]:
        self.game_state.phase = GamePhase.SETUP
        self.game_state.add_log("游戏开始！", public=True)
        print("📢 游戏开始！")
        
        if self.mode == "sandbox":
            print("\n" + "="*60)
            print("🎭 沙盒模式 - 所有玩家角色信息")
            print("="*60)
            for player in sorted(self.game_state.players.values(), key=lambda x: x.player_id):
                camp_icon = "🔴" if player.camp == Camp.WEREWOLF else "🟢"
                print(f"  {camp_icon} {player.name} - {player.role.name} ({player.camp.value}阵营)")
            print("="*60 + "\n")
        
        for player in self.game_state.players.values():
            if player.is_agent:
                engine = self.reasoning_engines[player.player_id]
                engine.memory_manager.record_game_event(
                    self.game_state,
                    f"游戏开始！你的角色是{player.role.name}"
                )
                
                all_players = self.game_state.get_alive_players()
                player_names = [p.name for p in all_players]
                engine.memory_manager.record_game_event(
                    self.game_state,
                    f"场上所有玩家是：{', '.join(player_names)}"
                )
                
                if player.camp == Camp.WEREWOLF:
                    werewolves = self.game_state.get_werewolves()
                    wolf_names = [w.name for w in werewolves]
                    engine.memory_manager.record_game_event(
                        self.game_state,
                        f"你的狼队友是：{', '.join(wolf_names)}",
                    )
        
        return {"game_state": self.game_state}
    
    def _night_phase(self, state: Dict[str, Any]) -> Dict[str, Any]:
        self.game_state.phase = GamePhase.NIGHT
        self.game_state.night_count += 1
        self.game_state.reset_night_actions()
        night_msg = f"第 {self.game_state.night_count} 夜，天黑请闭眼..."
        self.game_state.add_log(night_msg, public=True)
        print(f"🌙 {night_msg}")
        
        if self.game_state.night_count == 1:
            self._cupid_action()
        
        self._werewolf_action()
        self._prophet_action()
        self._witch_action()
        self._guardian_action()
        
        self._resolve_night_kill()
        
        return {"game_state": self.game_state}
    
    def _cupid_action(self) -> None:
        cupid = next((p for p in self.game_state.players.values() if p.role_type == RoleType.CUPID and p.status == PlayerStatus.ALIVE), None)
        if not cupid:
            return
        
        if self.mode == "sandbox":
            print(f"\n💘 丘比特睁眼了！丘比特是：{cupid.name}")
        
        if cupid.is_agent:
            engine = self.reasoning_engines[cupid.player_id]
            alive_ids = self.game_state.get_alive_player_ids()
            alive_ids.remove(cupid.player_id)
            
            lover1, thinking = engine.choose_night_action("cupid_choose", alive_ids, show_thinking=self.mode == "sandbox")
            if self.mode == "sandbox" and thinking:
                print(f"\n  💭 {cupid.name} 的思考：")
                print(f"  {thinking}")
            if lover1:
                alive_ids.remove(lover1)
                lover2 = random.choice(alive_ids) if alive_ids else None
                if lover2:
                    self._set_lovers(lover1, lover2)
        else:
            self._request_user_input("丘比特请选择两名玩家成为情侣")
    
    def _set_lovers(self, player1_id: int, player2_id: int) -> None:
        player1 = self.game_state.get_player(player1_id)
        player2 = self.game_state.get_player(player2_id)
        
        if player1 and player2:
            player1.lovers.append(player2_id)
            player2.lovers.append(player1_id)
            self.game_state.cupid_lovers = (player1_id, player2_id)
            self.game_state.add_log(f"丘比特指定了情侣", public=False, visible_to=[player1_id, player2_id])
            if self.mode == "sandbox":
                print(f"\n  💘 丘比特让 {player1.name} 和 {player2.name} 成为了情侣！")
            
            for pid in [player1_id, player2_id]:
                if pid in self.reasoning_engines:
                    engine = self.reasoning_engines[pid]
                    other_name = player2.name if pid == player1_id else player1.name
                    engine.memory_manager.record_game_event(self.game_state, f"你和{other_name}成为了情侣！")
    
    def _werewolf_action(self) -> None:
        werewolves = self.game_state.get_werewolves()
        if not werewolves:
            return
        
        if self.mode == "sandbox":
            print(f"\n🐺 狼人睁眼了！当前狼人：{', '.join([w.name for w in werewolves])}")
        
        alive_ids = self.game_state.get_alive_player_ids()
        alive_ids = [pid for pid in alive_ids if self.game_state.get_player(pid).camp != Camp.WEREWOLF]
        
        if not alive_ids:
            return
        
        if len(werewolves) > 1:
            if self.mode == "sandbox":
                print(f"\n  💬 狼人开始讨论今晚要杀死谁...")
            
            discussion_history = ""
            for i, werewolf in enumerate(werewolves):
                if werewolf.is_agent:
                    engine = self.reasoning_engines[werewolf.player_id]
                    context = f"第 {self.game_state.night_count} 夜，作为狼人讨论今晚要杀死谁。当前存活的好人：{', '.join([self.game_state.get_player(pid).name for pid in alive_ids])}"
                    
                    discussion = engine.generate_werewolf_discussion(context, discussion_history)
                    
                    if self.mode == "sandbox":
                        print(f"\n  🗣️ {werewolf.name}：{discussion}")
                    
                    discussion_history += f"\n{werewolf.name}：{discussion}"
                else:
                    print(f"\n🐺 你是狼人！当前存活的好人：{', '.join([self.game_state.get_player(pid).name for pid in alive_ids])}")
                    if discussion_history:
                        print(f"  其他狼人的讨论：{discussion_history}")
                    discussion = self._request_user_input(f"请发表你的狼人讨论意见")
                    if discussion:
                        print(f"  🗣️ {werewolf.name}：{discussion}")
                        discussion_history += f"\n{werewolf.name}：{discussion}"
        
        if self.mode == "sandbox":
            print(f"\n  🗳️ 狼人开始投票决定杀死谁...")
        
        vote_counts = {}
        wolf_thinking = {}
        
        for werewolf in werewolves:
            if werewolf.is_agent:
                engine = self.reasoning_engines[werewolf.player_id]
                target_id, thinking = engine.choose_night_action("werewolf_kill", alive_ids, show_thinking=self.mode == "sandbox")
                
                if self.mode == "sandbox" and thinking:
                    print(f"\n  💭 {werewolf.name} 的思考：")
                    print(f"  {thinking}")
                
                if target_id:
                    if target_id not in vote_counts:
                        vote_counts[target_id] = 0
                    vote_counts[target_id] += 1
                    wolf_thinking[werewolf.player_id] = thinking
            else:
                print(f"\n🐺 你是狼人！请投票决定要杀死的玩家")
                print(f"  候选目标：{', '.join([self.game_state.get_player(pid).name for pid in alive_ids])}")
                target_id = self._request_user_vote("请选择要杀死的玩家", alive_ids)
                if target_id:
                    if target_id not in vote_counts:
                        vote_counts[target_id] = 0
                    vote_counts[target_id] += 1
        
        if self.mode == "sandbox":
            print(f"\n  📊 投票结果：")
            for target_id, count in vote_counts.items():
                target_name = self.game_state.get_player(target_id).name
                print(f"    {target_name}: {count}票")
        
        max_votes = -1
        target_id = None
        for tid, cnt in vote_counts.items():
            if cnt > max_votes:
                max_votes = cnt
                target_id = tid
        
        if target_id:
            self.game_state.werewolf_vote = target_id
            target = self.game_state.get_player(target_id)
            if self.mode == "sandbox" and target:
                print(f"\n  🗡️ 狼人投票决定杀死：{target.name}（{max_votes}票）")
            for werewolf in werewolves:
                if werewolf.player_id in self.reasoning_engines:
                    engine = self.reasoning_engines[werewolf.player_id]
                    engine.memory_manager.record_game_event(self.game_state, f"狼人决定杀死{target.name}")
    
    def _prophet_action(self) -> None:
        prophet = next((p for p in self.game_state.players.values() if p.role_type == RoleType.PROPHET and p.status == PlayerStatus.ALIVE), None)
        if not prophet:
            return
        
        if self.mode == "sandbox":
            print(f"\n🔮 预言家睁眼了！预言家是：{prophet.name}")
        
        if prophet.is_agent:
            engine = self.reasoning_engines[prophet.player_id]
            alive_ids = self.game_state.get_alive_player_ids()
            alive_ids.remove(prophet.player_id)
            
            if alive_ids:
                target_id, thinking = engine.choose_night_action("prophet_check", alive_ids, show_thinking=self.mode == "sandbox")
                if self.mode == "sandbox" and thinking:
                    print(f"\n  💭 {prophet.name} 的思考：")
                    print(f"  {thinking}")
                if target_id:
                    target = self.game_state.get_player(target_id)
                    is_werewolf = target.camp == Camp.WEREWOLF
                    self.game_state.prophet_check = (target_id, is_werewolf)
                    if self.mode == "sandbox":
                        result = "🔴 狼人" if is_werewolf else "🟢 好人"
                        print(f"\n  🔍 {prophet.name} 查验了 {target.name}，结果是：{result}")
                    engine.memory_manager.record_game_event(self.game_state, f"你查验了{target.name}，结果是{'狼人' if is_werewolf else '好人'}")
        else:
            alive_ids = self.game_state.get_alive_player_ids()
            alive_ids.remove(prophet.player_id)
            
            target_id = self._request_user_vote("预言家请选择要查验的玩家", alive_ids)
            if target_id:
                target = self.game_state.get_player(target_id)
                is_werewolf = target.camp == Camp.WEREWOLF
                self.game_state.prophet_check = (target_id, is_werewolf)
                
                result = "🔴 狼人" if is_werewolf else "🟢 好人"
                print(f"\n🔍 你查验了 {target.name}，结果是：{result}")
    
    def _witch_action(self) -> None:
        witch = next((p for p in self.game_state.players.values() if p.role_type == RoleType.WITCH and p.status == PlayerStatus.ALIVE), None)
        if not witch:
            return
        
        if self.mode == "sandbox":
            potion_status = "✅ 有解药" if witch.witch_has_potion else "❌ 无解药"
            poison_status = "✅ 有毒药" if witch.witch_has_poison else "❌ 无毒药"
            print(f"\n🧙 女巫睁眼了！女巫是：{witch.name}")
            print(f"  💊 药品状态：解药 {potion_status} | 毒药 {poison_status}")
        
        if witch.is_agent:
            engine = self.reasoning_engines[witch.player_id]
            
            if self.game_state.werewolf_vote and witch.witch_has_potion:
                target = self.game_state.get_player(self.game_state.werewolf_vote)
                if self.mode == "sandbox" and target:
                    print(f"  💀 女巫看到 {target.name} 被狼人杀死了")
                engine.memory_manager.record_observation(f"今晚{target.name}被狼人杀死了", 8)
                
                alive_ids = self.game_state.get_alive_player_ids()
                choice, thinking = engine.choose_night_action("witch_heal", [self.game_state.werewolf_vote, -1], show_thinking=self.mode == "sandbox")
                if self.mode == "sandbox" and thinking:
                    print(f"\n  💭 {witch.name} 关于解药的思考：")
                    print(f"  {thinking}")
                if choice == self.game_state.werewolf_vote:
                    self.game_state.witch_action = ("heal", self.game_state.werewolf_vote)
                    witch.witch_has_potion = False
                    if self.mode == "sandbox":
                        print(f"\n  💚 {witch.name} 使用了解药，救活了 {target.name}！")
                    engine.memory_manager.record_strategy("使用解药救人")
                elif self.mode == "sandbox":
                    print(f"\n  💔 {witch.name} 决定不使用解药")
            
            if not self.game_state.witch_action and witch.witch_has_poison:
                alive_ids = self.game_state.get_alive_player_ids()
                alive_ids.remove(witch.player_id)
                choice, thinking = engine.choose_night_action("witch_poison", alive_ids + [-1], show_thinking=self.mode == "sandbox")
                if self.mode == "sandbox" and thinking:
                    print(f"\n  💭 {witch.name} 关于毒药的思考：")
                    print(f"  {thinking}")
                if choice and choice != -1:
                    self.game_state.witch_action = ("poison", choice)
                    witch.witch_has_poison = False
                    target = self.game_state.get_player(choice)
                    if self.mode == "sandbox":
                        print(f"\n  💜 {witch.name} 使用了毒药，毒死了 {target.name}！")
                    engine.memory_manager.record_strategy(f"使用毒药毒死{target.name}")
                elif self.mode == "sandbox":
                    print(f"\n  💜 {witch.name} 决定不使用毒药")
        else:
            potion_status = "✅ 有解药" if witch.witch_has_potion else "❌ 无解药"
            poison_status = "✅ 有毒药" if witch.witch_has_poison else "❌ 无毒药"
            print(f"\n🧙 你是女巫！药品状态：解药 {potion_status} | 毒药 {poison_status}")
            
            if self.game_state.werewolf_vote and witch.witch_has_potion:
                target = self.game_state.get_player(self.game_state.werewolf_vote)
                print(f"💀 {target.name} 被狼人杀死了！")
                
                use_heal = self._request_user_input("是否使用解药？(y/n)")
                if use_heal and use_heal.lower() == "y":
                    self.game_state.witch_action = ("heal", self.game_state.werewolf_vote)
                    witch.witch_has_potion = False
                    print(f"💚 你使用了解药，救活了 {target.name}！")
            
            if not self.game_state.witch_action and witch.witch_has_poison:
                use_poison = self._request_user_input("是否使用毒药？(y/n)")
                if use_poison and use_poison.lower() == "y":
                    alive_ids = self.game_state.get_alive_player_ids()
                    alive_ids.remove(witch.player_id)
                    target_id = self._request_user_vote("请选择要毒死的玩家", alive_ids)
                    if target_id:
                        self.game_state.witch_action = ("poison", target_id)
                        witch.witch_has_poison = False
                        target = self.game_state.get_player(target_id)
                        print(f"💜 你使用了毒药，毒死了 {target.name}！")
    
    def _guardian_action(self) -> None:
        guardian = next((p for p in self.game_state.players.values() if p.role_type == RoleType.GUARDIAN and p.status == PlayerStatus.ALIVE), None)
        if not guardian:
            return
        
        if self.mode == "sandbox":
            last_guard_msg = ""
            if guardian.last_guarded:
                last_guarded_player = self.game_state.get_player(guardian.last_guarded)
                if last_guarded_player:
                    last_guard_msg = f" (上一晚守护了 {last_guarded_player.name}，今晚不能守护他)"
            print(f"\n🛡️ 守卫睁眼了！守卫是：{guardian.name}{last_guard_msg}")
        
        if guardian.is_agent:
            engine = self.reasoning_engines[guardian.player_id]
            alive_ids = self.game_state.get_alive_player_ids()
            
            if guardian.last_guarded:
                alive_ids = [pid for pid in alive_ids if pid != guardian.last_guarded]
            
            if alive_ids:
                target_id, thinking = engine.choose_night_action("guardian_protect", alive_ids, show_thinking=self.mode == "sandbox")
                if self.mode == "sandbox" and thinking:
                    print(f"\n  💭 {guardian.name} 的思考：")
                    print(f"  {thinking}")
                if target_id:
                    self.game_state.guardian_protect = target_id
                    guardian.last_guarded = target_id
                    target = self.game_state.get_player(target_id)
                    if self.mode == "sandbox" and target:
                        print(f"\n  🛡️ {guardian.name} 守护了 {target.name}！")
                    engine.memory_manager.record_strategy(f"守护了{target.name}")
        else:
            last_guard_msg = ""
            if guardian.last_guarded:
                last_guarded_player = self.game_state.get_player(guardian.last_guarded)
                if last_guarded_player:
                    last_guard_msg = f" (上一晚守护了 {last_guarded_player.name}，今晚不能守护他)"
            print(f"\n🛡️ 你是守卫！{last_guard_msg}")
            
            alive_ids = self.game_state.get_alive_player_ids()
            if guardian.last_guarded:
                alive_ids = [pid for pid in alive_ids if pid != guardian.last_guarded]
            
            if alive_ids:
                target_id = self._request_user_vote("请选择要守护的玩家", alive_ids)
                if target_id:
                    self.game_state.guardian_protect = target_id
                    guardian.last_guarded = target_id
                    target = self.game_state.get_player(target_id)
                    print(f"🛡️ 你守护了 {target.name}！")
    
    def _resolve_night_kill(self) -> None:
        kill_target = self.game_state.werewolf_vote
        
        original_wolf_target = self.game_state.werewolf_vote
        saved_by_guardian = False
        saved_by_witch = False
        
        if kill_target and self.game_state.guardian_protect == kill_target:
            kill_target = None
            saved_by_guardian = True
            self.game_state.add_log("守卫守护成功！", public=False)
        
        if kill_target and self.game_state.witch_action and self.game_state.witch_action[0] == "heal" and self.game_state.witch_action[1] == kill_target:
            kill_target = None
            saved_by_witch = True
            self.game_state.add_log("女巫使用了解药！", public=False)
        
        if kill_target:
            self.game_state.night_kill_target = kill_target
            victim = self.game_state.get_player(kill_target)
            if victim:
                print(f"💀 {victim.name} 被狼人杀死了")
                self.game_state.kill_player(kill_target, "被狼人杀死")
                self._notify_all_agents_death(victim, "被狼人杀死")
        elif original_wolf_target:
            victim = self.game_state.get_player(original_wolf_target)
            if victim:
                self._notify_wolves_target_saved(victim, saved_by_guardian, saved_by_witch)
        
        if self.game_state.witch_action and self.game_state.witch_action[0] == "poison":
            poison_target = self.game_state.witch_action[1]
            victim = self.game_state.get_player(poison_target)
            if victim:
                print(f"🧪 {victim.name} 被女巫毒死了")
                self.game_state.kill_player(poison_target, "被女巫毒死")
                self._notify_all_agents_death(victim, "被女巫毒死")
    
    def _day_phase(self, state: Dict[str, Any]) -> Dict[str, Any]:
        self.game_state.phase = GamePhase.DAY
        self.game_state.day_count += 1
        day_msg = f"第 {self.game_state.day_count} 天，天亮了！"
        self.game_state.add_log(day_msg, public=True)
        print(f"\n☀️ {day_msg}")
        
        if self.game_state.night_kill_target:
            victim = self.game_state.get_player(self.game_state.night_kill_target)
            death_msg = f"昨晚 {victim.name} 死亡了"
            self.game_state.add_log(death_msg, public=True)
            print(f"📢 {death_msg}")
        else:
            self.game_state.add_log("昨晚是平安夜！", public=True)
            print("📢 昨晚是平安夜！")
        
        self._day_discussion()
        
        return {"game_state": self.game_state}
    
    def _day_discussion(self) -> None:
        alive_players = self.game_state.get_alive_players()
        self.game_state.speaking_order = [p.player_id for p in alive_players]
        random.shuffle(self.game_state.speaking_order)
        
        print(f"\n💬 开始发言讨论...")
        
        if self.mode == "sandbox":
            print("\n当前存活玩家（含角色）：")
            for player in sorted(self.game_state.get_alive_players(), key=lambda x: x.player_id):
                camp_icon = "🔴" if player.camp == Camp.WEREWOLF else "🟢"
                print(f"  {camp_icon} {player.name} - {player.role.name}")
        
        for i, player_id in enumerate(self.game_state.speaking_order):
            player = self.game_state.get_player(player_id)
            if player.status != PlayerStatus.ALIVE:
                continue
            
            self.game_state.current_speaker = player_id
            
            if player.is_agent:
                if self.mode == "sandbox":
                    camp_icon = "🔴" if player.camp == Camp.WEREWOLF else "🟢"
                    print(f"\n[{i+1}/{len(self.game_state.speaking_order)}] {camp_icon} {player.name} ({player.role.name}) 正在思考...")
                else:
                    print(f"\n[{i+1}/{len(self.game_state.speaking_order)}] {player.name} 正在思考...")
                
                engine = self.reasoning_engines[player_id]
                speech, thinking = engine.generate_speech(f"现在是白天发言阶段，轮到你发言了", show_thinking=self.mode == "sandbox")
                
                if self.mode == "sandbox" and thinking:
                    print(f"\n  💭 {player.name} 的思考：")
                    print(f"  {thinking}")
                
                self.game_state.add_log(f"{player.name}：{speech}", public=True)
                print(f"\n🗣️ {player.name}：{speech}")
                
                for listener_id, listener_engine in self.reasoning_engines.items():
                    if listener_id != player_id:
                        listener_engine.process_public_message(player_id, speech)
            else:
                speech = self._request_user_input(f"轮到你发言了，请输入你的发言内容")
                if speech:
                    self.game_state.add_log(f"{player.name}：{speech}", public=True)
                    print(f"🗣️ {player.name}：{speech}")
                    for listener_id, listener_engine in self.reasoning_engines.items():
                        listener_engine.process_public_message(player_id, speech)
    
    def _voting_phase(self, state: Dict[str, Any]) -> Dict[str, Any]:
        self.game_state.phase = GamePhase.VOTING
        vote_msg = "现在开始投票！"
        self.game_state.add_log(vote_msg, public=True)
        print(f"\n🗳️ {vote_msg}")
        
        alive_players = self.game_state.get_alive_players()
        vote_candidates = [p.player_id for p in alive_players]
        
        if self.mode == "sandbox":
            print(f"  候选玩家：{', '.join([self.game_state.get_player(cid).name for cid in vote_candidates])}")
        
        for player in alive_players:
            if player.status == PlayerStatus.IDIOT_REVEALED:
                continue
            
            if player.is_agent:
                engine = self.reasoning_engines[player.player_id]
                vote_target, thinking = engine.choose_vote_target(vote_candidates, show_thinking=self.mode == "sandbox")
                
                if self.mode == "sandbox":
                    camp_icon = "🔴" if player.camp == Camp.WEREWOLF else "🟢"
                    print(f"\n  {camp_icon} {player.name} ({player.role.name}) 正在思考投给谁...")
                    if thinking:
                        print(f"\n  💭 {player.name} 的思考：")
                        print(f"  {thinking}")
                
                target_player = self.game_state.get_player(vote_target)
                self.game_state.add_log(f"{player.name} 投票给了 {target_player.name}", public=True)
                print(f"\n  ✅ {player.name} 投票给了 {target_player.name}")
                target_player.votes += 1
            else:
                vote_target = self._request_user_vote("请选择你要投票的玩家", vote_candidates)
                if vote_target:
                    target_player = self.game_state.get_player(vote_target)
                    self.game_state.add_log(f"{player.name} 投票给了 {target_player.name}", public=True)
                    print(f"  ✅ {player.name} 投票给了 {target_player.name}")
                    target_player.votes += 1
        
        max_votes = -1
        voted_out = None
        for player in alive_players:
            if player.votes > max_votes:
                max_votes = player.votes
                voted_out = player
            player.votes = 0
        
        if voted_out:
            out_msg = f"{voted_out.name} 被投票出局了！"
            self.game_state.add_log(out_msg, public=True)
            print(f"\n❌ {out_msg}")
            self.game_state.kill_player(voted_out.player_id, "被投票驱逐")
            self._notify_all_agents_death(voted_out, "被投票驱逐")
        
        return {"game_state": self.game_state}
    
    def _check_game_end(self, state: Dict[str, Any]) -> Dict[str, Any]:
        winner = self.game_state.check_game_over()
        return {"game_state": self.game_state, "winner": winner}
    
    def _should_continue(self, state: Dict[str, Any]) -> str:
        if state.get("winner"):
            winner = state["winner"]
            win_msg = f"游戏结束！{winner.value}阵营获胜！"
            self.game_state.add_log(win_msg, public=True)
            print(f"\n🏆 {win_msg}")
            
            if self.mode == "sandbox":
                print("\n" + "="*60)
                print("📊 最终玩家信息")
                print("="*60)
                for player in sorted(self.game_state.players.values(), key=lambda x: x.player_id):
                    camp_icon = "🔴" if player.camp == Camp.WEREWOLF else "🟢"
                    status_icon = "👤" if player.status == PlayerStatus.ALIVE else "💀"
                    print(f"  {camp_icon} {status_icon} {player.name} - {player.role.name} ({player.camp.value}阵营) - {player.status.value}")
                print("="*60)
            
            return "end"
        return "continue"
    
    def _notify_all_agents_death(self, dead_player: Player, reason: str) -> None:
        """通知所有存活的Agent有玩家死亡"""
        for player_id, engine in self.reasoning_engines.items():
            player = self.game_state.get_player(player_id)
            if player and player.status == PlayerStatus.ALIVE:
                engine.memory_manager.record_observation(
                    f"{dead_player.name} 死亡了！原因：{reason}",
                    importance=9
                )
    
    def _notify_wolves_target_saved(self, target: Player, saved_by_guardian: bool, saved_by_witch: bool) -> None:
        """通知所有狼人他们的目标被救了"""
        werewolves = self.game_state.get_werewolves()
        save_reason = ""
        if saved_by_guardian and saved_by_witch:
            save_reason = "被守卫和女巫救了"
        elif saved_by_guardian:
            save_reason = "被守卫守护了"
        elif saved_by_witch:
            save_reason = "被女巫救了"
        
        for wolf in werewolves:
            if wolf.player_id in self.reasoning_engines:
                engine = self.reasoning_engines[wolf.player_id]
                engine.memory_manager.record_observation(
                    f"我们要杀的 {target.name} {save_reason}，他还活着！",
                    importance=9
                )
    
    def _request_user_input(self, prompt: str) -> str:
        print(f"\n[玩家输入] {prompt}")
        return input("> ")
    
    def _request_user_vote(self, prompt: str, candidates: Optional[List[int]] = None) -> Optional[int]:
        if not candidates:
            candidates = self.game_state.get_alive_player_ids()
        
        print(f"\n[玩家投票] {prompt}")
        print("可选玩家：")
        for cid in candidates:
            player = self.game_state.get_player(cid)
            print(f"  {cid}. {player.name}")
        
        while True:
            try:
                choice = input("请输入玩家ID: ")
                cid = int(choice)
                if cid in candidates:
                    return cid
                print("无效的选择，请重新输入")
            except ValueError:
                print("请输入有效的数字")
    
    def run(self, player_configs: List[Dict[str, str]]) -> GameState:
        self.setup_players(player_configs)
        final_state = self.graph.invoke({})
        return final_state["game_state"]
