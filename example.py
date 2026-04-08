#!/usr/bin/env python3
"""使用示例 - 演示如何使用狼人杀游戏系统"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from game.graph import WerewolfGame


def simple_sandbox_example():
    """沙盒模式示例 - 观看AI玩游戏"""
    load_dotenv()
    
    print("初始化LLM...")
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        temperature=0.8
    )
    
    print("创建游戏（沙盒模式）...")
    game = WerewolfGame(
        llm=llm,
        player_count=6,
        mode="sandbox"
    )
    
    player_configs = [
        {"name": "Alice", "personality": "谨慎的分析者"},
        {"name": "Bob", "personality": "冲动的冒险者"},
        {"name": "Charlie", "personality": "幽默的搞笑者"},
        {"name": "Diana", "personality": "冷酷的策略家"},
        {"name": "Eve", "personality": "友善的合作者"},
        {"name": "Frank", "personality": "多疑的怀疑者"},
    ]
    
    print("开始游戏...")
    final_state = game.run(player_configs)
    
    print("\n" + "="*60)
    print("游戏结束！")
    print(f"获胜阵营: {final_state.game_winner}")
    print("="*60)


def participation_example():
    """参与模式示例 - 你也是玩家之一"""
    load_dotenv()
    
    print("初始化LLM...")
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        temperature=0.8
    )
    
    print("创建游戏（参与模式）...")
    game = WerewolfGame(
        llm=llm,
        player_count=6,
        mode="participation",
        user_player_index=0
    )
    
    player_configs = [
        {"name": "你", "personality": "普通玩家"},
        {"name": "张三", "personality": "智慧的军师"},
        {"name": "李四", "personality": "勇猛的武将"},
        {"name": "王五", "personality": "狡猾的谋士"},
        {"name": "赵六", "personality": "忠诚的守卫"},
        {"name": "钱七", "personality": "神秘的术士"},
    ]
    
    print("开始游戏...")
    final_state = game.run(player_configs)


if __name__ == "__main__":
    import sys
    
    print("选择运行模式:")
    print("1. 沙盒模式示例")
    print("2. 参与模式示例")
    print("3. 运行主程序（main.py）")
    
    choice = input("请选择 (1/2/3): ").strip()
    
    if choice == "1":
        simple_sandbox_example()
    elif choice == "2":
        participation_example()
    elif choice == "3":
        os.system("python main.py")
    else:
        print("无效选择")
