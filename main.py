#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from game.graph import WerewolfGame
from core.game_state import GameState


def get_llm(provider: str = "qwen") -> ChatOpenAI:
    """
    获取 LLM 实例

    参数:
        provider: 模型提供商
            - "qwen": 阿里云通义千问
            - "openai": OpenAI GPT
    """
    if provider == "qwen":
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("请设置 DASHSCOPE_API_KEY 环境变量！")
        model = os.getenv("MODEL_NAME", "qwen-plus")
        base_url = os.getenv("DASHSCOPE_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        return ChatOpenAI(
            model=model,
            temperature=0.8,
            api_key=api_key,
            base_url=base_url
        )
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("请设置 OPENAI_API_KEY 环境变量！")
        model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        return ChatOpenAI(
            model=model,
            temperature=0.8,
            api_key=api_key
        )
    else:
        raise ValueError(f"不支持的模型提供商: {provider}")


def print_game_state(game_state: GameState, mode: str = "sandbox") -> None:
    print("\n" + "="*60)
    print(f"游戏阶段: {game_state.phase.value}")
    print(f"第 {game_state.day_count} 天 / 第 {game_state.night_count} 夜")
    print("="*60)

    print("\n玩家状态:")
    for player in game_state.players.values():
        status_icon = "👤" if player.status.value == "alive" else "💀"
        if player.status.value == "idiot_revealed":
            status_icon = "🤪"

        role_info = f" [{player.role.name}]" if mode == "sandbox" else ""
        print(f"  {status_icon} {player.name}{' (你)' if not player.is_agent else ''}{role_info} - {player.status.value}")

    print("\n最近日志:")
    recent_logs = game_state.logs[-10:] if len(game_state.logs) > 10 else game_state.logs
    for log in recent_logs:
        print(f"  [{log.phase.value}] {log.message}")

    if game_state.game_winner:
        print(f"\n🎉 游戏结束！{game_state.game_winner.value}阵营获胜！🎉")


def get_default_player_configs(count: int = 9) -> list:
    defaults = [
        {"name": "张飞", "personality": "鲁莽的张飞"},
        {"name": "诸葛亮", "personality": "智慧的诸葛亮"},
        {"name": "曹操", "personality": "奸诈的曹操"},
        {"name": "刘备", "personality": "仁厚的刘备"},
        {"name": "关羽", "personality": "忠义的关羽"},
        {"name": "赵云", "personality": "勇猛的赵云"},
        {"name": "周瑜", "personality": "儒雅的周瑜"},
        {"name": "吕布", "personality": "无敌的吕布"},
        {"name": "貂蝉", "personality": "美丽的貂蝉"},
        {"name": "孙尚香", "personality": "勇敢的孙尚香"},
        {"name": "黄月英", "personality": "聪明的黄月英"},
        {"name": "甄姬", "personality": "优雅的甄姬"},
    ]
    return defaults[:count]


def customize_player_configs(count: int, user_index: int = None) -> list:
    """让玩家自定义每个角色的配置"""
    configs = []
    
    print(f"\n🎨 自定义 {count} 个玩家配置")
    print("="*60)
    print("\n提示：")
    print("- 直接回车使用默认值")
    print("- 预设性格可选：")
    print("  三国人物：鲁莽的张飞、智慧的诸葛亮、奸诈的曹操、仁厚的刘备、")
    print("          忠义的关羽、勇猛的赵云、儒雅的周瑜、无敌的吕布、")
    print("          美丽的貂蝉、勇敢的孙尚香、聪明的黄月英、优雅的甄姬")
    print("  通用性格：幽默的喜剧演员、冷酷的侦探、狡猾的狐狸、普通玩家")
    print("- 你也可以输入任意性格描述，例如：'高冷的御姐'、'可爱的萝莉'、")
    print("          '腹黑的正太'、'成熟的大叔'等，系统会自动为你生成！")
    print("="*60)
    
    default_configs = get_default_player_configs(count)
    
    for i in range(count):
        player_num = i + 1
        is_user = user_index is not None and i == user_index
        default_config = default_configs[i]
        
        print(f"\n--- 玩家 {player_num} ---")
        if is_user:
            print("⭐ 这是你的角色")
        
        default_name = default_config["name"]
        if is_user:
            default_name = "你"
        
        name_input = input(f"名字 (默认: {default_name}): ").strip()
        name = name_input if name_input else default_name
        
        default_personality = default_config["personality"]
        personality_input = input(f"性格描述 (默认: {default_personality}): ").strip()
        personality = personality_input if personality_input else default_personality
        
        configs.append({"name": name, "personality": personality})
    
    print("\n✅ 玩家配置完成！")
    return configs


def get_player_count() -> int:
    """让玩家选择游戏人数"""
    print("\n请选择游戏人数:")
    print("  1. 6人局 - 快速游戏")
    print("  2. 9人局 - 标准配置 (推荐)")
    print("  3. 12人局 - 完整游戏")
    
    while True:
        choice = input("\n请选择 (1/2/3): ").strip()
        if choice == "1":
            return 6
        elif choice == "2":
            return 9
        elif choice == "3":
            return 12
        print("无效选择，请重新输入")


def main():
    load_dotenv()

    print("="*60)
    print("🐺 多Agent狼人杀模拟沙盒 🐺")
    print("="*60)

    # 1. 选择模型提供商
    print("\n请选择使用的模型提供商:")
    print("  1. 通义千问 (Qwen) - 推荐，使用阿里云API")
    print("  2. OpenAI (GPT) - 需要OpenAI API Key")

    provider_choice = input("\n请选择 (1/2): ").strip()
    provider = "qwen" if provider_choice == "1" else "openai"

    # 2. 选择游戏模式
    print("\n请选择游戏模式:")
    print("  1. 沙盒模式 - 观看AI们玩，可以看到所有信息")
    print("  2. 参与模式 - 你也是玩家之一")

    mode_choice = input("\n请选择 (1/2): ").strip()
    mode = "sandbox" if mode_choice == "1" else "participation"

    # 3. 选择游戏人数
    player_count = get_player_count()

    # 4. 参与模式选择玩家位置
    user_index = None
    if mode == "participation":
        print(f"\n你想成为第几个玩家？(1-{player_count})")
        while True:
            try:
                user_input = input("请输入: ").strip()
                user_index = int(user_input) - 1
                if 0 <= user_index < player_count:
                    break
                print(f"请输入 1 到 {player_count} 之间的数字")
            except ValueError:
                print("请输入有效的数字")

    print(f"\n已选择: {'沙盒模式' if mode == 'sandbox' else '参与模式'} | "
          f"{player_count}人局 | 模型: {'通义千问' if provider == 'qwen' else 'OpenAI'}")

    # 5. 初始化 LLM
    print("\n正在初始化LLM...")
    try:
        llm = get_llm(provider)
        print(f"✅ LLM 初始化成功！使用模型: {os.getenv('MODEL_NAME', 'qwen-plus') if provider == 'qwen' else os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')}")
    except ValueError as e:
        print(f"❌ LLM 初始化失败: {e}")
        print("\n请确保已经：")
        print("1. 复制配置文件: cp .env.qwen .env")
        print("2. 在 .env 中填入你的 API Key")
        return

    # 6. 选择性格生成方式
    print("\n是否使用LLM动态生成性格提示词？(y/n)")
    print("  y - 使用LLM生成（较慢，更个性化）")
    print("  n - 使用预设性格（快速，推荐）")
    use_llm_personality = input("请选择 (y/n): ").strip().lower() == "y"

    # 7. 自定义玩家配置
    print("\n是否自定义玩家配置？(y/n)")
    print("  y - 自定义每个玩家的名字和性格")
    print("  n - 使用默认配置（三国人物）")
    customize = input("请选择 (y/n): ").strip().lower() == "y"

    if customize:
        player_configs = customize_player_configs(player_count, user_index)
    else:
        player_configs = get_default_player_configs(player_count)
        if mode == "participation" and user_index is not None:
            player_configs[user_index]["name"] = "你"

    # 8. 显示玩家配置
    print("\n📋 玩家配置:")
    for i, config in enumerate(player_configs, 1):
        is_user = mode == "participation" and i == user_index + 1
        print(f"  {i}. {config['name']} - {config['personality']}{' (你)' if is_user else ''}")

    # 9. 创建游戏
    print("\n正在创建游戏...")
    game = WerewolfGame(
        llm=llm,
        player_count=player_count,
        mode=mode,
        user_player_index=user_index,
        use_llm_personality=use_llm_personality
    )

    # 10. 确认开始
    confirm = input("\n确认开始游戏？(y/n): ").strip().lower()
    if confirm != "y":
        print("游戏取消")
        return

    # 11. 运行游戏
    try:
        final_state = game.run(player_configs)
    except KeyboardInterrupt:
        print("\n\n游戏被中断")
    except Exception as e:
        print(f"\n\n游戏出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
