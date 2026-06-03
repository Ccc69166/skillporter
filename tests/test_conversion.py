#!/usr/bin/env python3
"""
测试Skill转换
============

测试从Claude格式转换为WorkBuddy格式。
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from skillporter import auto_parse, render_skill, SkillPlatform

def test_conversion():
    """测试转换功能"""
    print("Testing skill conversion...")
    
    # 源文件路径
    source_path = Path("examples/claude_skill/SKILL.md")
    
    if not source_path.exists():
        print(f"✗ Source file not found: {source_path}")
        return False
    
    try:
        # 解析源skill
        print(f"1. Parsing source skill: {source_path}")
        skill = auto_parse(str(source_path))
        
        print(f"   ✓ Skill parsed: {skill.id}")
        print(f"   ✓ Name: {skill.name}")
        print(f"   ✓ Variables: {len(skill.variables)}")
        print(f"   ✓ Tools: {len(skill.allowed_tools)}")
        
        # 转换为WorkBuddy格式
        print("\n2. Converting to WorkBuddy format...")
        output_dir = Path("examples/workbuddy_skill")
        
        render_skill(skill, SkillPlatform.WORKBUDDY, output_dir)
        
        print(f"   ✓ Converted to: {output_dir}")
        
        # 检查输出文件
        skill_file = output_dir / "SKILL.md"
        if skill_file.exists():
            print(f"   ✓ Output file created: {skill_file}")
            
            # 读取并显示内容
            content = skill_file.read_text(encoding='utf-8')
            print(f"   ✓ File size: {len(content)} characters")
            
            # 显示前几行
            lines = content.split('\n')
            print(f"   ✓ First 10 lines:")
            for i, line in enumerate(lines[:10], 1):
                print(f"      {i:2}: {line}")
            
            return True
        else:
            print(f"   ✗ Output file not created")
            return False
            
    except Exception as e:
        print(f"✗ Conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_conversion()
    sys.exit(0 if success else 1)