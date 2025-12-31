# Development Guidelines

## Problem-Solving Approach

### Systematic Investigation
- Start with the most likely causes based on recent changes
- Always reason through problems step by step before proposing solutions
- Identify the root cause rather than treating symptoms
- When facing errors, trace through the entire flow to understand what's happening
- Use evidence-based reasoning: check logs, inspect code, verify assumptions
- Use systematic elimination: test one variable at a time

### Planning Changes
- When definitively asked to make a change, raise a concern if you see significant risks.
- When asked to address multiple unrelated changes, always plan one change at a time.
- When a change is complex, break down the change into small logical steps that can be easily verified.

### Confirmation Before Changes
- Always get confirmation before making changes, especially when multiple approaches are possible
- Show diffs or explain proposed changes when the impact is significant
- Ask clarifying questions when requirements are ambiguous
- Present options with trade-offs when multiple solutions exist

## Code Structure & Organization

### File Organization
- Group related functionality into cohesive modules
- Use clear, descriptive file and directory names
- Separate concerns: models, business logic, presentation, configuration
- Keep related files close together in the directory structure

### Code Style
- Write minimal, focused code that directly addresses the requirement
- Avoid over-engineering or adding unnecessary complexity
- Follow the single responsibility principle: one responsibility per class or method.
- Use composition over inheritance for data models
- Prefer explicit over implicit: clear variable names, obvious logic flow

### Naming Conventions
- Use descriptive names that explain purpose, not implementation
- Be consistent with existing codebase conventions
- Choose names that will be clear to future developers

## Implementing and Testing Changes
- Implement changes in the small logical steps defined in the planning stage
- Always ensure changes "compile" (e.g., no syntax errors)
- Do not test changes yourself unless asked to do

## Communication Style

### Explaining Solutions
- Lead with the conclusion, then provide supporting reasoning
- Use concrete examples and code snippets when helpful
- Explain the "why" behind decisions, not just the "what"
- Be concise but thorough: include necessary context without being verbose

### Presenting Changes
- Show diffs for significant changes before implementing
- Explain the impact and benefits of proposed changes
- Highlight any potential risks or trade-offs
- Group related changes together logically

### Error Communication
- Clearly state what went wrong and why
- Provide specific steps to reproduce or investigate
- Suggest concrete next steps or solutions
- Admit when you're uncertain and need more information

## Technical Preferences

### Error Handling
- Fail fast with clear error messages
- Log errors with sufficient context for debugging
- Handle edge cases gracefully
- Provide meaningful feedback to users

### Testing & Validation
- Test changes in the actual environment when possible
- Verify fixes address the root cause, not just symptoms
- Check for unintended side effects
- Use browser dev tools and server logs for validation

### Dependencies & Tools
- Prefer official libraries over wrappers when reliability is important
- Use the simplest solution that meets requirements
- Avoid adding dependencies unless they provide clear value
- Keep tooling consistent with project standards