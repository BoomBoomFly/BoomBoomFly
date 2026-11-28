# AGENTS.md — Global AI Development Guidelines

## 0. Precedence & Environment
- **Precedence:** Project-level guidelines override this file.
- **Inspect First:** Check build files and active runtime environment (venv/Conda/Docker/ROS) before building or testing. Never guess commands when unclear.

## 1. Development Mode
Default to **Research Prototype / Engineering Validation Mode** (unless specified otherwise).
- **Priorities:** Functional correctness > Debuggability > Development speed > Maintainability.
- **Authority:** The AI implements; the project owner holds final authority over scope, priorities, and architecture.

## 2. Task Boundaries
- **SHIT Principles:**
  - **S (Scope Creep):** Implement only requested changes and necessary related updates; do not refactor unrelated code.
  - **H (Hypothetical Hardening):** Do not add purposeless safety mechanisms, defensive logic, or speculative features.
  - **I (Intent Violation):** Follow instructions strictly (e.g., review-only means no code changes).
  - **T (Task Thrashing):** Do not repeat completed, still-valid work or verification without new evidence.
- **Stop Ladder:** Understand code & dependencies → Simplest complete solution → Close actual gaps only → Evaluate added value → Verify sufficiently & finish.

## 3. Code Design
- Prefer reusing and modifying existing code over adding abstractions, wrappers, dependencies, or parallel implementations.
- Validate external input at system boundaries only; avoid redundant internal checks.
- Keep main functions focused on the normal path; extract functions only for reuse, complex logic, or clear conceptual boundaries.
- Comment only on non-obvious constraints and decisions. Prefer subtraction over addition; never judge quality by diff size or line count.

## 4. Compilation & Verification
- **Incremental Builds:** Compile only affected modules and required dependencies; reuse artifacts and avoid clean/workspace-wide rebuilds (e.g., `--packages-select`/`--packages-up-to` in ROS 2, single-target builds in CMake/Cargo). Use single-threaded builds when resources are constrained.
- **Testing Strategy:** Complete implementation before comprehensive testing and simulation (necessary immediate compilation and interface checks allowed). Test real implementations, minimize mocks, and fix actual failures.
- **Workflow:** Understand → Implement → Incremental Build → Test/Simulate → Fix → Necessary Regression → Finish.

## 5. Research Order
Search the current codebase first. Trigger external research only for complex/unfamiliar features or non-obvious issues:
- **Feature Development:** Search GitHub for similar projects and implementations first.
- **Debugging:** Search developer communities first, then verify against official docs, GitHub Issues, and source code.
- Always verify compatibility with the current environment before adopting; never copy blindly.

## 6. Delivery
- Preserve established interfaces and technical decisions; never report planned features as completed.
- Present optional improvements as suggestions only—do not implement without authorization. Briefly report changes, build/test results, and known issues.

**General Principle:** Understand first, implement completely, verify afterward. Do all necessary work and nothing unnecessary; let complexity grow with actual requirements.