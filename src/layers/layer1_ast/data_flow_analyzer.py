"""Data Flow Analyzer for state and constant tracking.

This module analyzes AST nodes to extract data flow information
including state reads/writes, constants, and function calls.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.core.entities.behavioral_model import DataFlowInfo, NodeType

if TYPE_CHECKING:
    from src.core.entities.behavioral_model import ASTNode


class DataFlowAnalyzer:
    """Analyzes data flow in AST representations.

    Extracts information about:
    - State variables read and written
    - Constants defined
    - Imports
    - Function calls
    - Type definitions
    - Global references
    """

    def __init__(self) -> None:
        """Initialize the data flow analyzer."""
        self._state_reads: set[str] = set()
        self._state_writes: set[str] = set()
        self._constants: list[Any] = []
        self._imports: set[str] = set()
        self._function_calls: set[str] = set()
        self._type_definitions: set[str] = set()
        self._global_refs: set[str] = set()

        # Track assignment targets for context
        self._in_assignment = False
        self._current_assignment_target: str | None = None

    def analyze(self, ast: ASTNode) -> DataFlowInfo:
        """Analyze data flow in an AST.

        Args:
            ast: The AST root node

        Returns:
            DataFlowInfo with extracted information
        """
        # Reset state
        self._state_reads = set()
        self._state_writes = set()
        self._constants = []
        self._imports = set()
        self._function_calls = set()
        self._type_definitions = set()
        self._global_refs = set()

        # Traverse and analyze
        self._analyze_node(ast)

        return DataFlowInfo(
            state_reads=tuple(sorted(self._state_reads)),
            state_writes=tuple(sorted(self._state_writes)),
            constants=tuple(self._constants),
            imports=tuple(sorted(self._imports)),
            function_calls=tuple(sorted(self._function_calls)),
            type_definitions=tuple(sorted(self._type_definitions)),
            global_refs=tuple(sorted(self._global_refs)),
        )

    def _analyze_node(self, node: ASTNode) -> None:
        """Recursively analyze an AST node.

        Args:
            node: The AST node to analyze
        """
        node_type = node.node_type

        if node_type == NodeType.IMPORT:
            self._analyze_import(node)
        elif node_type == NodeType.ASSIGNMENT:
            self._analyze_assignment(node)
        elif node_type == NodeType.CONSTANT:
            self._analyze_constant(node)
        elif node_type == NodeType.NAME:
            self._analyze_name(node)
        elif node_type == NodeType.CALL:
            self._analyze_call(node)
        elif node_type == NodeType.FUNCTION:
            self._analyze_function(node)
        elif node_type == NodeType.CLASS:
            self._analyze_class(node)
        elif node_type == NodeType.ATTRIBUTE:
            self._analyze_attribute(node)

        # Recurse into children
        for child in node.children:
            self._analyze_node(child)

    def _analyze_import(self, node: ASTNode) -> None:
        """Analyze an import node.

        Args:
            node: Import AST node
        """
        if node.name:
            self._imports.add(node.name)

        # Check metadata for additional import info
        metadata = node.metadata
        if "module" in metadata:
            self._imports.add(metadata["module"])
        if "names" in metadata:
            for name in metadata["names"]:
                self._imports.add(name)

    def _analyze_assignment(self, node: ASTNode) -> None:
        """Analyze an assignment node.

        Args:
            node: Assignment AST node
        """
        target_name = node.name

        if target_name:
            # Record as state write
            self._state_writes.add(target_name)

            # Check if it's a constant (uppercase name)
            if target_name.isupper():
                # Get the value if available
                if node.value is not None:
                    self._constants.append(node.value)
                elif node.children:
                    # Try to extract value from first child
                    for child in node.children:
                        if child.node_type == NodeType.CONSTANT:
                            self._constants.append(child.value)
                            break

            # Check if it's a global
            if target_name.isupper() or target_name.startswith("_"):
                self._global_refs.add(target_name)

        # Check for type annotation
        if node.metadata.get("type_annotation"):
            self._type_definitions.add(str(node.metadata["type_annotation"]))

        # Analyze the value being assigned (context: in assignment)
        self._in_assignment = True
        self._current_assignment_target = target_name
        for child in node.children:
            self._analyze_node(child)
        self._in_assignment = False
        self._current_assignment_target = None

    def _analyze_constant(self, node: ASTNode) -> None:
        """Analyze a constant node.

        Args:
            node: Constant AST node
        """
        if node.value is not None:
            # Only track constants assigned to named variables
            if self._in_assignment and self._current_assignment_target:
                if self._current_assignment_target.isupper():
                    self._constants.append(node.value)

    def _analyze_name(self, node: ASTNode) -> None:
        """Analyze a name reference node.

        Args:
            node: Name AST node
        """
        name = node.name or str(node.value)

        if name:
            # Skip Python built-ins and keywords
            builtins = {
                "True",
                "False",
                "None",
                "print",
                "len",
                "range",
                "str",
                "int",
                "float",
                "list",
                "dict",
                "set",
                "tuple",
                "type",
                "isinstance",
                "hasattr",
                "getattr",
                "setattr",
            }

            if name not in builtins:
                # If in assignment context and not the target, it's a read
                if self._in_assignment and name != self._current_assignment_target:
                    self._state_reads.add(name)
                elif not self._in_assignment:
                    self._state_reads.add(name)

                # Check if it looks like a global/constant reference
                if name.isupper():
                    self._global_refs.add(name)

    def _analyze_call(self, node: ASTNode) -> None:
        """Analyze a function call node.

        Args:
            node: Call AST node
        """
        func_name = node.name

        if func_name:
            self._function_calls.add(func_name)
        elif node.metadata.get("function"):
            self._function_calls.add(str(node.metadata["function"]))

        # Check for method calls in children
        for child in node.children:
            if child.node_type == NodeType.ATTRIBUTE:
                attr_name = child.name
                if attr_name:
                    self._function_calls.add(attr_name)

    def _analyze_function(self, node: ASTNode) -> None:
        """Analyze a function definition node.

        Args:
            node: Function AST node
        """
        # Check for type annotations
        metadata = node.metadata

        if metadata.get("return_type"):
            self._type_definitions.add(str(metadata["return_type"]))

        if metadata.get("parameters"):
            for param in metadata["parameters"]:
                if isinstance(param, dict) and param.get("type"):
                    self._type_definitions.add(str(param["type"]))

    def _analyze_class(self, node: ASTNode) -> None:
        """Analyze a class definition node.

        Args:
            node: Class AST node
        """
        class_name = node.name
        if class_name:
            self._type_definitions.add(class_name)

    def _analyze_attribute(self, node: ASTNode) -> None:
        """Analyze an attribute access node.

        Args:
            node: Attribute AST node
        """
        attr_name = node.name

        if attr_name:
            # Check if it's a state attribute access
            if node.metadata.get("object"):
                obj_name = str(node.metadata["object"])
                full_name = f"{obj_name}.{attr_name}"

                if self._in_assignment:
                    self._state_writes.add(full_name)
                else:
                    self._state_reads.add(full_name)
