---
author: Senior Developer
description: A skill for reviewing code quality and suggesting improvements
description_en: A skill for reviewing code quality and suggesting improvements
description_zh: 代码审查技能，用于审查代码质量并提出改进建议
id: code-review
name: Code Review Skill
tags:
- code-review
- quality
- best-practices
version: 1.0.0
---

# Code Review Skill

This skill helps you review code quality and suggest improvements.

## Instructions

1. **Read the code file**: Use the `Read` tool to read the code file specified by the user.

2. **Analyze code quality**: Look for the following issues:
   - Code style violations
   - Potential bugs
   - Performance issues
   - Security vulnerabilities
   - Code duplication
   - Missing documentation

3. **Check for best practices**: Verify that the code follows:
   - Language-specific best practices
   - Design patterns
   - SOLID principles
   - DRY principle

4. **Provide suggestions**: Offer specific, actionable suggestions for improvement.

5. **Ask for context**: If needed, use `AskUserQuestion` to understand:
   - The purpose of the code
   - Target audience
   - Performance requirements
   - Security requirements

## Variables

- `{{args}}`: The code file path or directory to review
- `{{context}}`: Additional context about the code review

## Example Usage

```bash
# Review a single file
skillporter import claude code-review
skillporter convert code-review workbuddy
skillporter sync code-review workbuddy

# Review a directory
skillporter import claude code-review --name "my-review"
```

## Notes

- This skill works best with Python, JavaScript, TypeScript, and Java code
- For large codebases, consider reviewing one file at a time
- Use the `Glob` and `Grep` tools to find related files