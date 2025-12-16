#!/usr/bin/env python3
"""
HVAC Insulation Estimation Skill for Claude Agent SDK

This module provides a standalone Agent SDK skill for estimating HVAC insulation
projects. It wraps the existing estimation engine into a reusable skill that can
be integrated with any Claude API application.

Usage:
    from hvac_insulation_skill import HVACInsulationSkill

    skill = HVACInsulationSkill(api_key="your-anthropic-api-key")
    result = skill.run("Extract project info from specs.pdf")
"""

import os
import json
from typing import Dict, Any, List, Optional
from anthropic import Anthropic
from claude_agent_tools import (
    extract_project_info,
    extract_specifications,
    extract_measurements,
    validate_specifications,
    cross_reference_data,
    calculate_pricing,
    generate_quote,
    get_tool_schemas
)


class HVACInsulationSkill:
    """
    Agent SDK skill for HVAC insulation estimation.

    This skill provides comprehensive tools for:
    - Extracting project information from documents
    - Extracting insulation specifications
    - Extracting measurements from mechanical drawings
    - Validating specifications against industry standards
    - Cross-referencing specifications and measurements
    - Calculating material quantities and pricing
    - Generating professional quotes

    Attributes:
        client: Anthropic API client
        model: Claude model to use (default: claude-sonnet-4-5-20250929)
        tools: Dictionary of available tool functions
        tool_schemas: OpenAPI schemas for tool definitions
        session_data: Storage for extracted data across tool calls
        conversation_history: Message history for the agent
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-5-20250929",
        max_tokens: int = 8192
    ):
        """
        Initialize the HVAC Insulation Estimation skill.

        Args:
            api_key: Anthropic API key (if None, reads from ANTHROPIC_API_KEY env var)
            model: Claude model to use
            max_tokens: Maximum tokens for responses

        Raises:
            ValueError: If API key is not provided and not found in environment
        """
        # Get API key
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key required. Provide via api_key parameter or "
                "set ANTHROPIC_API_KEY environment variable."
            )

        # Initialize Anthropic client
        self.client = Anthropic(api_key=self.api_key)
        self.model = model
        self.max_tokens = max_tokens

        # Register tools
        self.tools = {
            "extract_project_info": extract_project_info,
            "extract_specifications": extract_specifications,
            "extract_measurements": extract_measurements,
            "validate_specifications": validate_specifications,
            "cross_reference_data": cross_reference_data,
            "calculate_pricing": calculate_pricing,
            "generate_quote": generate_quote,
        }

        # Get tool schemas
        self.tool_schemas = get_tool_schemas()

        # Initialize session data storage
        self.session_data = {
            "project_info": None,
            "specifications": [],
            "measurements": [],
            "pricing": None,
            "quote": None,
            "uploaded_files": {}
        }

        # Initialize conversation history
        self.conversation_history = []

        # System prompt
        self.system_prompt = self._get_system_prompt()

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the HVAC insulation estimation agent."""
        return """You are an expert HVAC insulation estimation assistant with deep knowledge of:
- Mechanical systems (HVAC ducts, pipes, equipment)
- Insulation materials (fiberglass, elastomeric, cellular glass, etc.)
- Industry standards (ASHRAE, SMACNA, mechanical codes)
- Construction documentation (specifications, drawings, schedules)
- Material pricing and labor estimation

Your role is to help users:
1. Extract project information from construction documents
2. Identify insulation specifications from spec sections
3. Measure HVAC systems from mechanical drawings
4. Validate specifications against industry standards
5. Cross-reference specifications with measurements
6. Calculate material quantities and pricing
7. Generate professional project quotes

You have access to specialized tools for each of these tasks. Use them systematically
to analyze documents and provide accurate estimates.

When analyzing documents:
- Be thorough and detail-oriented
- Note any ambiguities or missing information
- Provide confidence scores for extracted data
- Flag potential issues or conflicts
- Suggest clarifications when needed

Always maintain professionalism and focus on accuracy."""

    def run(
        self,
        user_message: str,
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """
        Run the skill with a user message.

        This is the main entry point for interacting with the skill. The agent
        will process the message, use tools as needed, and return results.

        Args:
            user_message: The user's request or question
            max_iterations: Maximum tool use iterations to prevent infinite loops

        Returns:
            Dictionary containing:
                - success: Boolean indicating if request completed successfully
                - response: The agent's text response
                - session_data: Current session data (project_info, specs, etc.)
                - tool_calls: List of tools that were called
                - iterations: Number of tool use iterations

        Example:
            >>> skill = HVACInsulationSkill(api_key="your-key")
            >>> result = skill.run("Extract project info from /path/to/specs.pdf")
            >>> print(result['response'])
            >>> print(result['session_data']['project_info'])
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        iterations = 0
        tool_calls = []

        try:
            # Agent loop
            while iterations < max_iterations:
                # Call Claude API
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    system=self.system_prompt,
                    tools=self.tool_schemas,
                    messages=self.conversation_history
                )

                # Add assistant response to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response.content
                })

                # Check stop reason
                if response.stop_reason == "end_turn":
                    # Extract text response
                    text_response = self._extract_text_from_content(response.content)

                    return {
                        "success": True,
                        "response": text_response,
                        "session_data": self.session_data,
                        "tool_calls": tool_calls,
                        "iterations": iterations,
                        "stop_reason": "end_turn"
                    }

                elif response.stop_reason == "tool_use":
                    # Execute tools and continue loop
                    tool_results = self._execute_tools(response.content)
                    tool_calls.extend([
                        {"tool": block.name, "iteration": iterations}
                        for block in response.content
                        if hasattr(block, 'type') and block.type == "tool_use"
                    ])

                    # Add tool results to history
                    self.conversation_history.append({
                        "role": "user",
                        "content": tool_results
                    })

                    iterations += 1

                elif response.stop_reason == "max_tokens":
                    # Handle max tokens case
                    text_response = self._extract_text_from_content(response.content)

                    return {
                        "success": False,
                        "response": text_response,
                        "session_data": self.session_data,
                        "tool_calls": tool_calls,
                        "iterations": iterations,
                        "stop_reason": "max_tokens",
                        "error": "Response truncated due to max tokens limit"
                    }

                else:
                    # Unexpected stop reason
                    return {
                        "success": False,
                        "response": f"Unexpected stop reason: {response.stop_reason}",
                        "session_data": self.session_data,
                        "tool_calls": tool_calls,
                        "iterations": iterations,
                        "stop_reason": response.stop_reason
                    }

            # Max iterations reached
            return {
                "success": False,
                "response": "Maximum tool use iterations reached",
                "session_data": self.session_data,
                "tool_calls": tool_calls,
                "iterations": iterations,
                "stop_reason": "max_iterations",
                "error": f"Reached maximum of {max_iterations} iterations"
            }

        except Exception as e:
            return {
                "success": False,
                "response": f"Error: {str(e)}",
                "session_data": self.session_data,
                "tool_calls": tool_calls,
                "iterations": iterations,
                "error": str(e)
            }

    def _execute_tools(self, content_blocks: List) -> List[Dict[str, Any]]:
        """
        Execute tool calls from Claude's response.

        Args:
            content_blocks: List of content blocks from Claude's response

        Returns:
            List of tool result dictionaries for the next API call
        """
        tool_results = []

        for block in content_blocks:
            if hasattr(block, 'type') and block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input

                try:
                    # Execute the tool
                    if tool_name in self.tools:
                        result = self.tools[tool_name](**tool_input)

                        # Update session data
                        self._update_session_data(tool_name, result)

                        # Format result for Claude
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result, default=str)
                        })
                    else:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps({
                                "success": False,
                                "error": f"Unknown tool: {tool_name}"
                            })
                        })

                except Exception as e:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps({
                            "success": False,
                            "error": str(e)
                        })
                    })

        return tool_results

    def _update_session_data(self, tool_name: str, result: Dict[str, Any]) -> None:
        """
        Update session data based on tool execution results.

        Args:
            tool_name: Name of the tool that was executed
            result: Result dictionary from the tool
        """
        if not result.get("success"):
            return

        data = result.get("data", {})

        # Update session data based on tool type
        if tool_name == "extract_project_info":
            self.session_data["project_info"] = data

        elif tool_name == "extract_specifications":
            self.session_data["specifications"] = data.get("specifications", [])

        elif tool_name == "extract_measurements":
            self.session_data["measurements"] = data.get("measurements", [])

        elif tool_name == "calculate_pricing":
            self.session_data["pricing"] = data

        elif tool_name == "generate_quote":
            self.session_data["quote"] = data

    def _extract_text_from_content(self, content_blocks: List) -> str:
        """
        Extract text content from Claude's response blocks.

        Args:
            content_blocks: List of content blocks from Claude's response

        Returns:
            Combined text from all text blocks
        """
        text_parts = []

        for block in content_blocks:
            if hasattr(block, 'type') and block.type == "text":
                text_parts.append(block.text)

        return "\n".join(text_parts)

    def reset_session(self) -> None:
        """
        Reset the session data and conversation history.

        This is useful when starting a new project estimation.
        """
        self.session_data = {
            "project_info": None,
            "specifications": [],
            "measurements": [],
            "pricing": None,
            "quote": None,
            "uploaded_files": {}
        }
        self.conversation_history = []

    def get_session_data(self) -> Dict[str, Any]:
        """
        Get the current session data.

        Returns:
            Dictionary containing all extracted and calculated data
        """
        return self.session_data.copy()

    def export_session(self, filepath: str) -> None:
        """
        Export session data to a JSON file.

        Args:
            filepath: Path where to save the session data
        """
        with open(filepath, 'w') as f:
            json.dump({
                "session_data": self.session_data,
                "conversation_history": [
                    {
                        "role": msg["role"],
                        "content": str(msg["content"])
                    }
                    for msg in self.conversation_history
                ]
            }, f, indent=2, default=str)

    def import_session(self, filepath: str) -> None:
        """
        Import session data from a JSON file.

        Args:
            filepath: Path to the session data file
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
            self.session_data = data.get("session_data", {})
            # Note: conversation_history is not restored to avoid complications

    def get_available_tools(self) -> List[Dict[str, str]]:
        """
        Get list of available tools with descriptions.

        Returns:
            List of dictionaries with tool names and descriptions
        """
        return [
            {
                "name": schema["name"],
                "description": schema["description"]
            }
            for schema in self.tool_schemas
        ]

    def call_tool_directly(
        self,
        tool_name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call a tool directly without using the agent loop.

        This is useful for programmatic access to individual tools.

        Args:
            tool_name: Name of the tool to call
            **kwargs: Tool-specific parameters

        Returns:
            Tool result dictionary

        Example:
            >>> skill = HVACInsulationSkill(api_key="your-key")
            >>> result = skill.call_tool_directly(
            ...     "extract_project_info",
            ...     pdf_path="/path/to/specs.pdf"
            ... )
        """
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}. Available tools: {list(self.tools.keys())}"
            }

        try:
            result = self.tools[tool_name](**kwargs)
            self._update_session_data(tool_name, result)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Convenience functions for common workflows

def quick_estimate(
    pdf_path: str,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Quick estimation workflow for a single PDF document.

    This function performs a complete estimation workflow:
    1. Extract project information
    2. Extract specifications
    3. Extract measurements
    4. Validate specifications
    5. Cross-reference data
    6. Calculate pricing
    7. Generate quote

    Args:
        pdf_path: Path to the PDF document (specs or drawings)
        api_key: Anthropic API key (optional if set in environment)

    Returns:
        Dictionary with complete estimation results

    Example:
        >>> result = quick_estimate("/path/to/project.pdf")
        >>> print(result['quote'])
    """
    skill = HVACInsulationSkill(api_key=api_key)

    # Run complete estimation
    result = skill.run(
        f"Please perform a complete HVAC insulation estimation for the document at {pdf_path}. "
        f"Extract project information, specifications, and measurements, then validate, "
        f"cross-reference, calculate pricing, and generate a quote."
    )

    return result


def extract_specs_only(
    pdf_path: str,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extract only specifications from a document.

    Args:
        pdf_path: Path to the specification PDF
        api_key: Anthropic API key (optional if set in environment)

    Returns:
        Dictionary with extracted specifications
    """
    skill = HVACInsulationSkill(api_key=api_key)
    result = skill.call_tool_directly("extract_specifications", pdf_path=pdf_path)
    return result


def extract_measurements_only(
    pdf_path: str,
    scale: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extract only measurements from mechanical drawings.

    Args:
        pdf_path: Path to the mechanical drawing PDF
        scale: Drawing scale (e.g., "1/4\" = 1'")
        api_key: Anthropic API key (optional if set in environment)

    Returns:
        Dictionary with extracted measurements
    """
    skill = HVACInsulationSkill(api_key=api_key)
    params = {"pdf_path": pdf_path}
    if scale:
        params["scale"] = scale
    result = skill.call_tool_directly("extract_measurements", **params)
    return result


if __name__ == "__main__":
    # Example usage
    print("HVAC Insulation Estimation Skill")
    print("=" * 50)
    print("\nThis is a Claude Agent SDK skill for HVAC insulation estimation.")
    print("\nUsage:")
    print("  from hvac_insulation_skill import HVACInsulationSkill")
    print("  skill = HVACInsulationSkill(api_key='your-key')")
    print("  result = skill.run('Extract specs from project.pdf')")
    print("\nAvailable tools:")

    # Show available tools (without requiring API key)
    from claude_agent_tools import get_tool_schemas
    schemas = get_tool_schemas()
    for i, schema in enumerate(schemas, 1):
        print(f"  {i}. {schema['name']}: {schema['description'][:60]}...")
