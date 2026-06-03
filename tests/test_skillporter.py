#!/usr/bin/env python3
"""
SkillPorter测试脚本
==================

用于验证SkillPorter安装和基本功能是否正常工作。

运行方式：
    python test_skillporter.py
    
    或者使用pytest：
    pytest test_skillporter.py -v

测试内容：
1. 模块导入测试
2. 配置管理测试
3. 解析器测试
4. 渲染器测试
5. CLI测试

作者：Senior Developer (高级开发工程师)
版本：1.0.0
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# 添加项目路径到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_import():
    """测试模块导入"""
    print("Testing module imports...")
    
    try:
        # 测试核心模块导入
        from skillporter import UniversalSkill, SkillPlatform
        from skillporter import auto_parse, get_parser
        from skillporter import render_skill, convert_skill, get_renderer
        from skillporter import ConfigManager, get_config
        from skillporter import SkillPorterCLI, main
        
        print("✓ Core modules imported successfully")
        
        # 测试平台模块导入
        from skillporter import ClaudeParser, ClaudeRenderer
        from skillporter import CodexParser, CodexRenderer
        from skillporter import WorkBuddyParser, WorkBuddyRenderer
        
        print("✓ Platform modules imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_config():
    """测试配置管理"""
    print("\nTesting configuration management...")
    
    try:
        from skillporter import ConfigManager
        
        # 创建临时配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_path = f.name
        
        try:
            # 测试配置管理器
            config_manager = ConfigManager(config_path)
            config = config_manager.load_config()
            
            print(f"✓ Config loaded: {config_path}")
            print(f"  Version: {config.version}")
            print(f"  LLM enabled: {config.llm.enabled}")
            
            # 测试配置更新
            config_manager.update_config(verbose=True)
            config_manager.save_config()
            
            print("✓ Config updated and saved")
            
            return True
            
        finally:
            # 清理临时文件
            if os.path.exists(config_path):
                os.unlink(config_path)
                
    except Exception as e:
        print(f"✗ Config test failed: {e}")
        return False


def test_schema():
    """测试USS数据结构"""
    print("\nTesting Universal Skill Schema...")
    
    try:
        from skillporter import UniversalSkill, SkillPlatform
        
        # 创建测试skill
        skill = UniversalSkill(
            id="test-skill",
            name="Test Skill",
            description="A test skill for SkillPorter",
            instructions="# Test Instructions\n\nThis is a test skill.",
            source_platform=SkillPlatform.WORKBUDDY
        )
        
        # 测试序列化
        skill_dict = skill.to_dict()
        skill_json = skill.to_json()
        skill_yaml = skill.to_yaml()
        
        print(f"✓ Skill created: {skill.id}")
        print(f"  Dict keys: {len(skill_dict)}")
        print(f"  JSON length: {len(skill_json)}")
        print(f"  YAML length: {len(skill_yaml)}")
        
        # 测试反序列化
        skill_from_dict = UniversalSkill.from_dict(skill_dict)
        skill_from_json = UniversalSkill.from_json(skill_json)
        skill_from_yaml = UniversalSkill.from_yaml(skill_yaml)
        
        print("✓ Deserialization successful")
        
        # 测试验证
        errors = skill.validate()
        if errors:
            print(f"  Validation errors: {errors}")
        else:
            print("✓ Validation passed")
        
        return True
        
    except Exception as e:
        print(f"✗ Schema test failed: {e}")
        return False


def test_parser():
    """测试解析器"""
    print("\nTesting parsers...")
    
    try:
        from skillporter import auto_parse, get_parser, SkillPlatform
        
        # 测试获取解析器
        claude_parser = get_parser(SkillPlatform.CLAUDE)
        codex_parser = get_parser(SkillPlatform.CODEX)
        workbuddy_parser = get_parser(SkillPlatform.WORKBUDDY)
        
        print("✓ Parsers retrieved:")
        print(f"  Claude: {claude_parser}")
        print(f"  Codex: {codex_parser}")
        print(f"  WorkBuddy: {workbuddy_parser}")
        
        # 创建测试skill文件
        test_dir = tempfile.mkdtemp()
        skill_file = Path(test_dir) / "SKILL.md"
        
        skill_content = """---
id: test-skill
name: Test Skill
description: A test skill
allowed-tools:
  - Read
  - Write
  - Bash
---

# Test Instructions

This is a test skill with $ARGUMENTS variable.
"""
        
        skill_file.write_text(skill_content, encoding='utf-8')
        
        try:
            # 测试解析
            skill = auto_parse(str(skill_file))
            print(f"✓ Skill parsed: {skill.id}")
            print(f"  Name: {skill.name}")
            print(f"  Variables: {len(skill.variables)}")
            print(f"  Tools: {len(skill.allowed_tools)}")
            
            return True
            
        finally:
            # 清理测试目录
            shutil.rmtree(test_dir)
                
    except Exception as e:
        print(f"✗ Parser test failed: {e}")
        return False


def test_renderer():
    """测试渲染器"""
    print("\nTesting renderers...")
    
    try:
        from skillporter import UniversalSkill, SkillPlatform, get_renderer
        
        # 创建测试skill
        skill = UniversalSkill(
            id="test-skill",
            name="Test Skill",
            description="A test skill",
            instructions="# Test Instructions\n\nThis is a test skill with $ARGUMENTS variable.",
            source_platform=SkillPlatform.WORKBUDDY
        )
        
        # 添加工具权限
        skill.add_tool("Read", "read")
        skill.add_tool("Write", "write")
        skill.add_tool("Bash", "bash")
        
        # 测试渲染器
        claude_renderer = get_renderer(SkillPlatform.CLAUDE)
        codex_renderer = get_renderer(SkillPlatform.CODEX)
        workbuddy_renderer = get_renderer(SkillPlatform.WORKBUDDY)
        
        print("✓ Renderers retrieved:")
        print(f"  Claude: {claude_renderer}")
        print(f"  Codex: {codex_renderer}")
        print(f"  WorkBuddy: {workbuddy_renderer}")
        
        # 测试转换
        claude_files = claude_renderer.render_skill(skill)
        codex_files = codex_renderer.render_skill(skill)
        workbuddy_files = workbuddy_renderer.render_skill(skill)
        
        print("✓ Skills rendered:")
        print(f"  Claude files: {list(claude_files.keys())}")
        print(f"  Codex files: {list(codex_files.keys())}")
        print(f"  WorkBuddy files: {list(workbuddy_files.keys())}")
        
        return True
        
    except Exception as e:
        print(f"✗ Renderer test failed: {e}")
        return False


def test_cli():
    """测试CLI"""
    print("\nTesting CLI...")
    
    try:
        from skillporter import SkillPorterCLI
        
        # 创建CLI实例
        cli = SkillPorterCLI()
        
        print("✓ CLI created successfully")
        
        # 测试帮助信息
        try:
            cli.run(["--help"])
        except SystemExit:
            # argparse会调用sys.exit，这是正常的
            pass
        
        print("✓ CLI help displayed")
        
        return True
        
    except Exception as e:
        print(f"✗ CLI test failed: {e}")
        return False


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("SkillPorter Test Suite")
    print("=" * 60)
    
    tests = [
        ("Import", test_import),
        ("Config", test_config),
        ("Schema", test_schema),
        ("Parser", test_parser),
        ("Renderer", test_renderer),
        ("CLI", test_cli)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # 打印总结
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:15} : {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! SkillPorter is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())