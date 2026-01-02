---
name: Quality Vectors in Code Comments
description: Quality vectors for code comments
---

Analyze whether the comment meets the following criteria:

Code Comment Quality Review Guide

1. **Does it provide real value?**
   - Does it explain the "why" instead of just the "what"?
   - Does it clarify non-obvious decisions or complex business logic?
   - Or does it simply repeat what the code already clearly states?
2. **Is it necessary or redundant?**
   - Is the code so self-explanatory that the comment is unnecessary?
   - Could the code be improved (variable/function names) to eliminate the need for the comment?
   - Does it add context that the code alone cannot express?
3. **Will it stand the test of time?**
   - Will it remain valid after refactoring?
   - Is it abstract enough to survive implementation changes?
   - Or does it describe technical details that will soon change, becoming "documentary technical debt"?
4. **Is it concise without omitting critical details?**
   - Does it balance brevity with completeness?
   - Does it include enough information to understand the full context?
   - Does it avoid unnecessary verbosity while maintaining clarity?
5. **Is it accurate and explanatory?**
   - Does it accurately describe what the code does?
   - Does it explain special cases, edge cases, or non-obvious behaviors?
   - Does it use appropriate technical language without ambiguity?
   - Does it document limitations, assumptions, or important dependencies?
