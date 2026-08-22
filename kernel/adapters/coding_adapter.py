"""Coding capability adapter for the JARVIS Kernel."""

from __future__ import annotations

import ast
import textwrap
from typing import Any

from kernel.interfaces.capability_adapter import (
    CapabilityAdapter,
    CapabilityResult,
    CapabilityTask,
)
from kernel.interfaces.storage import Storage


class CodingAdapter(CapabilityAdapter):
    """Framework-independent coding capability adapter."""

    def __init__(self, storage: Storage | None = None) -> None:
        self._storage = storage
        self._initialized = False

    @property
    def name(self) -> str:
        return "coding"

    @property
    def capability_type(self) -> str:
        return "coding"

    @property
    def description(self) -> str:
        return "Provides code generation, explanation, and review capabilities."

    async def initialize(self) -> None:
        self._initialized = True

    async def health_check(self) -> bool:
        return self._initialized

    def supports(self, intent: str) -> bool:
        return intent.lower() in {
            "code",
            "coding",
            "generate_code",
            "explain_code",
            "review_code",
            "refactor_code",
            "debug_code",
            "test_code",
        }

    async def execute(self, task: CapabilityTask) -> CapabilityResult:
        if not self._initialized:
            raise RuntimeError("CodingAdapter has not been initialized.")

        intent = task.intent.lower()

        # Route to appropriate handler
        if intent == "generate_code":
            return await self._handle_generate_code(task)
        elif intent == "explain_code":
            return await self._handle_explain_code(task)
        elif intent == "review_code":
            return await self._handle_review_code(task)
        elif intent == "refactor_code":
            return await self._handle_refactor_code(task)
        elif intent == "debug_code":
            return await self._handle_debug_code(task)
        elif intent == "test_code":
            return await self._handle_test_code(task)
        elif intent in ("code", "coding"):
            return await self._handle_generic_coding(task)
        else:
            return self._failed(
                task,
                f"Intent '{task.intent}' is not supported by the coding adapter.",
            )

    def _ok(self, task: CapabilityTask, *, data: dict[str, Any], message: str | None = None) -> CapabilityResult:
        result_data = {
            "intent": task.intent,
            "payload": task.payload,
            **data,
        }
        if message is not None:
            result_data["message"] = message

        return CapabilityResult(
            success=True,
            data=result_data,
            metadata={
                "adapter": self.name,
                "status": "ok",
            },
            execution_time_ms=0.0,
        )


    def _failed(self, task: CapabilityTask, error: str) -> CapabilityResult:
        return CapabilityResult(
            success=False,
            error=error,
            metadata={
                "adapter": self.name,
                "status": "error",
            },
            execution_time_ms=0.0,
        )
    async def _handle_generate_code(self, task: CapabilityTask) -> CapabilityResult:
        """Generate deterministic code based on simple patterns."""
        payload = task.payload
        language = payload.get("language", "python")
        prompt = payload.get("prompt") or payload.get("user_input", "")

        if not prompt:
            # Default to a simple function generation for generic coding requests
            prompt = "function"

        if language.lower() != "python":
            return self._failed(
                task,
                f"Language '{language}' not supported. Only Python is currently supported."
            )

        # Simple deterministic code generation based on keywords
        prompt_lower = prompt.lower()

        if "hello world" in prompt_lower:
            code = 'print("Hello, World!")'
        elif "factorial" in prompt_lower:
            code = textwrap.dedent('''
                def factorial(n: int) -> int:
                    """Calculate factorial of n."""
                    if n < 0:
                        raise ValueError("Factorial is not defined for negative numbers")
                    if n == 0 or n == 1:
                        return 1
                    return n * factorial(n - 1)
            ''').strip()
        elif "fibonacci" in prompt_lower:
            code = textwrap.dedent('''
                def fibonacci(n: int) -> int:
                    """Calculate nth Fibonacci number."""
                    if n < 0:
                        raise ValueError("Fibonacci is not defined for negative numbers")
                    if n == 0:
                        return 0
                    if n == 1:
                        return 1
                    a, b = 0, 1
                    for _ in range(n - 1):
                        a, b = b, a + b
                    return b
            ''').strip()
        elif "class" in prompt_lower:
            # Extract class name if possible
            words = prompt.split()
            class_name = "MyClass"
            for i, word in enumerate(words):
                if word.lower() == "class" and i + 1 < len(words):
                    class_name = words[i + 1].strip(":,.")
                    break

            code = textwrap.dedent(f'''
                class {class_name}:
                    """A simple class."""

                    def __init__(self):
                        """Initialize the class."""
                        self.value = 0

                    def get_value(self) -> int:
                        """Get the current value."""
                        return self.value

                    def set_value(self, value: int) -> None:
                        """Set the value."""
                        self.value = value
            ''').strip()
        elif "function" in prompt_lower or "def" in prompt_lower:
            # Extract function name if possible
            words = prompt.split()
            func_name = "my_function"
            for i, word in enumerate(words):
                if word.lower() in ("function", "def") and i + 1 < len(words):
                    func_name = words[i + 1].strip(":,()")
                    break

            code = textwrap.dedent(f'''
                def {func_name}() -> None:
                    """A simple function."""
                    pass
            ''').strip()
        else:
            # Default simple function
            code = textwrap.dedent('''
                def main() -> None:
                    """Main function."""
                    print("Hello from generated code!")

            if __name__ == "__main__":
                main()
            ''').strip()

        return self._ok(
            task,
            data={
                "generated_code": code,
                "language": language,
                "explanation": f"Generated {language} code based on prompt: '{prompt}'",
            },
            message="Generated code",
        )

    async def _handle_explain_code(self, task: CapabilityTask) -> CapabilityResult:
        """Explain Python code using AST analysis."""
        payload = task.payload
        code = payload.get("code", "")
        file_path = payload.get("path")

        # Get code from file if path provided
        if file_path and not code:
            if not self._storage:
                return self._failed(task, "Storage not available for file operations")

            try:
                code = self._storage.read_text(str(file_path))
            except Exception as exc:
                return self._failed(task, f"Failed to read file: {exc}")

        if not code:
            return self._failed(task, "Missing 'code' in payload and no file path provided")

        try:
            # Parse the code
            tree = ast.parse(code)

            # Generate explanation
            explanation_parts = []

            # Check for module docstring
            if (tree.body and isinstance(tree.body[0], ast.Expr) and
                isinstance(tree.body[0].value, ast.Constant) and
                isinstance(tree.body[0].value.value, str)):
                explanation_parts.append(f"Module docstring: {tree.body[0].value.value}")

            # Count different types of nodes
            functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]

            if imports:
                explanation_parts.append(f"Found {len(imports)} import statement(s)")

            if classes:
                class_names = [cls.name for cls in classes]
                explanation_parts.append(f"Defined classes: {', '.join(class_names)}")

                # Explain each class briefly
                for cls in classes:
                    methods = [node for node in cls.body if isinstance(node, ast.FunctionDef)]
                    if methods:
                        method_names = [m.name for m in methods]
                        explanation_parts.append(
                            f"Class '{cls.name}' has methods: {', '.join(method_names)}"
                        )
                    else:
                        explanation_parts.append(f"Class '{cls.name}' has no methods")

            if functions:
                # Filter out methods (functions inside classes)
                module_functions = [
                    f for f in functions
                    if not any(isinstance(f, ast.FunctionDef) and
                             f in [node for node in ast.walk(cls) if isinstance(node, ast.FunctionDef)]
                             for cls in classes)
                ]

                if module_functions:
                    func_names = [f.name for f in module_functions]
                    explanation_parts.append(f"Defined functions: {', '.join(func_names)}")

                    # Explain each function briefly
                    for func in module_functions:
                        args = [arg.arg for arg in func.args.args]
                        explanation_parts.append(
                            f"Function '{func.name}' takes arguments: {', '.join(args) if args else 'none'}"
                        )

            if not explanation_parts:
                explanation_parts.append("Code parsed successfully but contains no significant structures")

            explanation = "; ".join(explanation_parts)

            return self._ok(
                task,
                data={
                    "explanation": explanation,
                    "code_length": len(code),
                    "line_count": len(code.splitlines()),
                },
            )

        except SyntaxError as exc:
            return self._failed(
                task,
                f"Invalid Python syntax: {exc.msg} at line {exc.lineno}, column {exc.offset}"
            )
        except Exception as exc:
            return self._failed(task, f"Failed to explain code: {exc}")

    async def _handle_review_code(self, task: CapabilityTask) -> CapabilityResult:
        """Review Python code for common issues."""
        payload = task.payload
        code = payload.get("code", "")
        file_path = payload.get("path")

        # Get code from file if path provided
        if file_path and not code:
            if not self._storage:
                return self._failed(task, "Storage not available for file operations")

            try:
                code = self._storage.read_text(str(file_path))
            except Exception as exc:
                return self._failed(task, f"Failed to read file: {exc}")

        if not code:
            return self._failed(task, "Missing 'code' in payload and no file path provided")

        issues = []

        try:
            tree = ast.parse(code)

            # Check for common issues
            for node in ast.walk(tree):
                # Check for bare except clauses
                if isinstance(node, ast.ExceptHandler) and node.type is None:
                    issues.append({
                        "type": "bare_except",
                        "message": "Bare except clause detected",
                        "line": getattr(node, 'lineno', 0),
                        "column": getattr(node, 'col_offset', 0)
                    })

                # Check for hardcoded passwords/secrets (simple pattern)
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    s = node.value.lower()
                    if any(keyword in s for keyword in ['password', 'secret', 'key', 'token']):
                        if len(s) > 8:  # Likely a real value, not just a variable name
                            issues.append({
                                "type": "hardcoded_secret",
                                "message": "Potential hardcoded secret detected",
                                "line": getattr(node, 'lineno', 0),
                                "column": getattr(node, 'col_offset', 0)
                            })

                # Check for TODO/FIXME comments (in string constants that look like comments)
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    s = node.value
                    if any(keyword in s.upper() for keyword in ['TODO', 'FIXME', 'HACK', 'XXX']):
                        issues.append({
                            "type": "todo_comment",
                            "message": f"TODO/FIXME comment detected: {s[:50]}...",
                            "line": getattr(node, 'lineno', 0),
                            "column": getattr(node, 'col_offset', 0)
                        })

            # Additional checks using source lines
            lines = code.splitlines()
            for i, line in enumerate(lines, 1):
                # Check for print statements (might be debug code)
                if 'print(' in line and not line.strip().startswith('#'):
                    issues.append({
                        "type": "print_statement",
                        "message": "Print statement found - consider using logging",
                        "line": i,
                        "column": line.find('print(')
                    })

                # Check for long lines
                if len(line) > 100:
                    issues.append({
                        "type": "long_line",
                        "message": f"Line too long ({len(line)} characters)",
                        "line": i,
                        "column": min(100, len(line))
                    })

        except SyntaxError as exc:
            return self._failed(
                task,
                f"Invalid Python syntax: {exc.msg} at line {exc.lineno}, column {exc.offset}"
            )
        except Exception as exc:
            return self._failed(task, f"Failed to review code: {exc}")

        # Determine overall assessment
        if not issues:
            assessment = "No issues found"
            status = "good"
        elif len(issues) <= 3:
            assessment = f"Found {len(issues)} minor issue(s)"
            status = "fair"
        else:
            assessment = f"Found {len(issues)} issues that may need attention"
            status = "needs_improvement"

        return self._ok(
            task,
            data={
                "assessment": assessment,
                "status": status,
                "issues": issues,
                "issue_count": len(issues),
            },
            message="Code review completed",
        )

    async def _handle_refactor_code(self, task: CapabilityTask) -> CapabilityResult:
        """Perform deterministic refactoring operations."""
        payload = task.payload
        code = payload.get("code", "")
        file_path = payload.get("path")
        operation = payload.get("operation", "").lower()

        # Get code from file if path provided
        if file_path and not code:
            if not self._storage:
                return self._failed(task, "Storage not available for file operations")

            try:
                code = self._storage.read_text(str(file_path))
            except Exception as exc:
                return self._failed(task, f"Failed to read file: {exc}")

        if not code:
            return self._failed(task, "Missing 'code' in payload and no file path provided")

        if not operation:
            return self._failed(task, "Missing 'operation' in payload for refactoring")

        try:
            tree = ast.parse(code)

            if operation == "rename_variable":
                old_name = payload.get("old_name")
                new_name = payload.get("new_name")

                if not old_name or not new_name:
                    return self._failed(task, "Both 'old_name' and 'new_name' required for rename_variable operation")

                # Simple variable renaming (limited scope)
                # This is a basic implementation - a full refactor would need more sophisticated handling
                lines = code.splitlines()
                changed_lines = []
                changes_made = 0

                for line in lines:
                    # Simple replacement - be careful not to break strings
                    if old_name in line:
                        # More sophisticated replacement would be needed for production
                        # This is a simplified version for demonstration
                        new_line = line.replace(old_name, new_name)
                        if new_line != line:
                            changes_made += 1
                        changed_lines.append(new_line)
                    else:
                        changed_lines.append(line)

                new_code = '\n'.join(changed_lines)

                # Validate that the new code is still syntactically valid
                try:
                    ast.parse(new_code)
                except SyntaxError:
                    return self._failed(
                        task,
                        "Refactoring would produce invalid Python syntax"
                    )

                return self._ok(
                    task,
                    data={
                        "refactored_code": new_code,
                        "changes_made": changes_made,
                        "operation": "rename_variable",
                        "old_name": old_name,
                        "new_name": new_name,
                    },
                )

            elif operation == "extract_function":
                # This would require more sophisticated analysis
                return self._failed(
                    task,
                    "Extract function refactoring not yet implemented"
                )

            else:
                return self._failed(
                    task,
                    f"Unsupported refactoring operation: {operation}. Supported operations: rename_variable"
                )

        except SyntaxError as exc:
            return self._failed(
                task,
                f"Invalid Python syntax: {exc.msg} at line {exc.lineno}, column {exc.offset}"
            )
        except Exception as exc:
            return self._failed(task, f"Failed to refactor code: {exc}")

    async def _handle_debug_code(self, task: CapabilityTask) -> CapabilityResult:
        """Debug Python code by analyzing syntax and runtime errors."""
        payload = task.payload
        code = payload.get("code", "")
        file_path = payload.get("path")
        error_info = payload.get("error", "")

        # Get code from file if path provided
        if file_path and not code:
            if not self._storage:
                return self._failed(task, "Storage not available for file operations")

            try:
                code = self._storage.read_text(str(file_path))
            except Exception as exc:
                return self._failed(task, f"Failed to read file: {exc}")

        if not code and not error_info:
            return self._failed(task, "Missing 'code' in payload, no file path provided, and no error info")

        debug_info = {
            "syntax_valid": False,
            "syntax_error": None,
            "analysis": [],
        }

        # Check syntax first
        if code:
            try:
                tree = ast.parse(code)
                debug_info["syntax_valid"] = True
                debug_info["analysis"].append("Code syntax is valid")
            except SyntaxError as exc:
                debug_info["syntax_valid"] = False
                debug_info["syntax_error"] = {
                    "message": exc.msg,
                    "line": exc.lineno,
                    "column": exc.offset,
                }
                debug_info["analysis"].append(
                    f"Syntax error: {exc.msg} at line {exc.lineno}, column {exc.offset}"
                )

        # If we have error info, analyze it
        if error_info:
            debug_info["analysis"].append(f"Provided error information: {error_info}")

            # Simple error pattern matching
            error_lower = error_info.lower()
            if "division by zero" in error_lower or "zerodivisionerror" in error_lower:
                debug_info["analysis"].append("Possible division by zero error")
            elif "index out of range" in error_lower or "indexerror" in error_lower:
                debug_info["analysis"].append("Possible index out of range error")
            elif "key error" in error_lower or "keyerror" in error_lower:
                debug_info["analysis"].append("Possible key error - missing dictionary key")
            elif "attribute error" in error_lower or "attributeerror" in error_lower:
                debug_info["analysis"].append("Possible attribute error - accessing non-existent attribute")
            elif "import error" in error_lower or "importerror" in error_lower:
                debug_info["analysis"].append("Possible import error - module not found")
            elif "name error" in error_lower or "nameerror" in error_lower:
                debug_info["analysis"].append("Possible name error - undefined variable")

        # Provide suggestions based on analysis
        suggestions = []
        if not debug_info["syntax_valid"]:
            suggestions.append("Fix the syntax error before running the code")
        elif "division by zero" in str(debug_info).lower():
            suggestions.append("Add a check for zero before division")
        elif "index out of range" in str(debug_info).lower():
            suggestions.append("Check array/list bounds before accessing elements")
        elif "key error" in str(debug_info).lower():
            suggestions.append("Use .get() method or check if key exists before accessing")
        elif "attribute error" in str(debug_info).lower():
            suggestions.append("Check if object has the attribute before accessing it")
        elif "import error" in str(debug_info).lower():
            suggestions.append("Verify the module is installed and correctly named")
        elif "name error" in str(debug_info).lower():
            suggestions.append("Check variable names for typos and ensure they are defined")

        if not suggestions and debug_info["syntax_valid"]:
            suggestions.append("Code appears syntactically valid - check runtime logic")

        return self._ok(
            task,
            data={
                "debug_info": debug_info,
                "suggestions": suggestions,
            },
            message="Debug analysis completed",
        )

    async def _handle_test_code(self, task: CapabilityTask) -> CapabilityResult:
        """Generate test skeletons for Python code."""
        payload = task.payload
        code = payload.get("code", "")
        file_path = payload.get("path")
        framework = payload.get("framework", "pytest").lower()

        # Get code from file if path provided
        if file_path and not code:
            if not self._storage:
                return self._failed(task, "Storage not available for file operations")

            try:
                code = self._storage.read_text(str(file_path))
            except Exception as exc:
                return self._failed(task, f"Failed to read file: {exc}")

        if not code:
            return self._failed(task, "Missing 'code' in payload and no file path provided")

        try:
            tree = ast.parse(code)

            # Extract functions and classes to test
            functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

            # Filter out nested functions (methods)
            module_functions = [
                f for f in functions
                if not any(isinstance(f, ast.FunctionDef) and
                         f in [node for node in ast.walk(cls) if isinstance(node, ast.FunctionDef)]
                         for cls in classes)
            ]

            test_code_parts = []

            if framework == "pytest":
                test_code_parts.append("import pytest")
                test_code_parts.append("")

                # Add import for the module being tested (if we had a filename)
                if file_path:
                    # Extract module name from file path
                    import os
                    module_name = os.path.splitext(os.path.basename(file_path))[0]
                    test_code_parts.append(f"import {module_name}")
                    test_code_parts.append("")

                # Generate test functions
                for func in module_functions:
                    func_name = func.name
                    args = [arg.arg for arg in func.args.args]

                    test_code_parts.append(f"def test_{func_name}():")
                    test_code_parts.append(f'    """Test for {func_name} function."""')

                    if args:
                        # Generate placeholder assertions
                        test_code_parts.append(f'    # TODO: Implement test for {func_name}')
                        test_code_parts.append(f'    # Arguments: {", ".join(args)}')
                        test_code_parts.append(f'    # Example: assert {func_name}(...) == expected_value')
                        test_code_parts.append(f'    assert True  # Placeholder - replace with actual test')
                    else:
                        test_code_parts.append(f'    # TODO: Implement test for {func_name}')
                        test_code_parts.append(f'    assert True  # Placeholder - replace with actual test')

                    test_code_parts.append("")

                # Generate test classes
                for cls in classes:
                    class_name = cls.name
                    methods = [node for node in cls.body if isinstance(node, ast.FunctionDef)]

                    test_code_parts.append(f"class Test{class_name}:")
                    test_code_parts.append(f'    """Test suite for {class_name} class."""')

                    if methods:
                        for method in methods:
                            method_name = method.name
                            test_code_parts.append(f"    def test_{method_name}(self):")
                            test_code_parts.append(f'        """Test for {method_name} method."""')
                            test_code_parts.append(f'        # TODO: Implement test for {method_name}')
                            test_code_parts.append(f'        assert True  # Placeholder - replace with actual test')
                            test_code_parts.append("")
                    else:
                        test_code_parts.append(f'    def test_{class_name.lower()}_instantiation(self):')
                        test_code_parts.append(f'        """Test {class_name} instantiation."""')
                        test_code_parts.append(f'        # TODO: Implement test for {class_name}')
                        test_code_parts.append(f'        assert True  # Placeholder - replace with actual test')
                        test_code_parts.append("")

                # If no functions or classes found, create a basic test
                if not module_functions and not classes:
                    test_code_parts.append("def test_basic():")
                    test_code_parts.append('    """Basic placeholder test."""')
                    test_code_parts.append("    assert True  # Replace with actual test")

            elif framework == "unittest":
                test_code_parts.append("import unittest")
                test_code_parts.append("")

                if file_path:
                    import os
                    module_name = os.path.splitext(os.path.basename(file_path))[0]
                    test_code_parts.append(f"import {module_name}")
                    test_code_parts.append("")

                test_code_parts.append("class TestGenerated(unittest.TestCase):")
                test_code_parts.append('    """Test case for generated tests."""')

                for func in module_functions:
                    func_name = func.name
                    test_code_parts.append(f"    def test_{func_name}(self):")
                    test_code_parts.append(f'        """Test for {func_name} function."""')
                    test_code_parts.append(f'        # TODO: Implement test for {func_name}')
                    test_code_parts.append(f'        self.assertTrue(True)  # Placeholder')
                    test_code_parts.append("")

                if not module_functions and not classes:
                    test_code_parts.append("    def test_basic(self):")
                    test_code_parts.append('        """Basic placeholder test."""')
                    test_code_parts.append("        self.assertTrue(True)  # Replace with actual test")

                test_code_parts.append("")
                test_code_parts.append("if __name__ == '__main__':")
                test_code_parts.append("    unittest.main()")
            else:
                return self._failed(
                    task,
                    f"Unsupported test framework: {framework}. Supported frameworks: pytest, unittest"
                )

            test_code = '\n'.join(test_code_parts)

            return self._ok(
                task,
                data={
                    "test_code": test_code,
                    "framework": framework,
                    "functions_found": len(module_functions),
                    "classes_found": len(classes),
                },
            )

        except SyntaxError as exc:
            return self._failed(
                task,
                f"Invalid Python syntax: {exc.msg} at line {exc.lineno}, column {exc.offset}"
            )
        except Exception as exc:
            return self._failed(task, f"Failed to generate test code: {exc}")

    async def _handle_generic_coding(self, task: CapabilityTask) -> CapabilityResult:
        """Handle generic coding requests."""
        # For generic requests, try to determine intent from payload
        payload = task.payload
        if "code" in payload or "prompt" in payload or "user_input" in payload:
            # Treat as generate_code if we have code, prompt, or user_input
            return await self._handle_generate_code(task)
        elif "explain" in str(payload).lower():
            return await self._handle_explain_code(task)
        elif "review" in str(payload).lower():
            return await self._handle_review_code(task)
        else:
            # Default to generate_code with a generic prompt
            return await self._handle_generate_code(task)

    async def shutdown(self) -> None:
        self._initialized = False
