#!/usr/bin/env python3
"""
测试Codex格式转换
================

测试从Claude格式转换为Codex格式。
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from skillporter import auto_parse, render_skill, SkillPlatform

def test_codex_conversion():
    """测试Codex转换功能"""
    print("Testing Codex format conversion...")
    
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
        
        # 转换为Codex格式
        print("\n2. Converting to Codex format...")
        output_dir = Path("examples/codex_skill")
        
        render_skill(skill, SkillPlatform.CODEX, output_dir)
        
        print(f"   ✓ Converted to: {output_dir}")
        
        # 检查输出文件
        openai_yaml = output_dir / "openai.yaml"
        agents_md = output_dir / "AGENTS.md"
        
        if openai_yaml.exists():
            print(f"   ✓ openai.yaml created: {openai_yaml}")
            
            # 读取并显示内容
            content = openai_yaml.read_text(encoding='utf-8')
            print(f"   ✓ File size: {len(content)} characters")
            
            # 显示前几行
            lines = content.split('\n')
            print(f"   ✓ First 10 lines:")
            for i, line in enumerate(lines[:10], 1):
                print(f"      {i:2}: {line}")
        else:
            print(f"   ✗ openai.yaml not created")
            return False
        
        if agents_md.exists():
            print(f"\n   ✓ AGENTS.md created: {agents_md}")
            
            # 读取并显示内容
            content = agents_md.read_text(encoding='utf-8')
            print(f"   ✓ File size: {len(content)} characters")
            
            # 显示前几行
            lines = content.split('\n')
            print(f"   ✓ First 10 lines:")
            for i, line in enumerate(lines[:10], 1):
                print(f"      {i:2}: {line}")
        else:
            print(f"\n   ⚠ AGENTS.md not created (optional)")
        
        return True
            
    except Exception as e:
        print(f"✗ Conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_codex_conversion()
    sys.exit(0 if success else 1)