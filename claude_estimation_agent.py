"""
Claude Estimation Agent
=======================

Main orchestrator for the intelligent insulation estimation agent.
Manages conversation flow, tool execution, and multi-turn reasoning.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from datetime import datetime

from anthropic import Anthropic

# Import our tool implementations
from claude_agent_tools import AGENT_TOOLS, get_tool_schemas


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InsulationEstimationAgent:
    """
    Main agent orchestrator for insulation estimation workflow.

    This agent provides conversational interface to the estimation system
    with intelligent tool use, validation, and recommendations.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096
    ):
        """
        Initialize the estimation agent.

        Args:
            api_key: Anthropic API key (reads from ANTHROPIC_API_KEY env var if not provided)
            model: Claude model to use
            max_tokens: Maximum tokens per response
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be provided or set in environment")

        self.client = Anthropic(api_key=self.api_key)
        self.model = model
        self.max_tokens = max_tokens

        # Conversation state
        self.conversation_history: List[Dict] = []
        self.session_data: Dict[str, Any] = {
            "project_info": None,
            "specifications": [],
            "measurements": [],
            "pricing": None,
            "quote": None,
            "uploaded_files": {}
        }

        # Tool registry
        self.tools = AGENT_TOOLS
        self.tool_schemas = get_tool_schemas()

        logger.info(f"Initialized InsulationEstimationAgent with model {self.model}")

    @property
    def system_prompt(self) -> str:
        """
        System prompt defining the agent's role and capabilities.
        """
        return """
You are an expert HVAC insulation estimator with deep knowledge of:
- Mechanical insulation specifications and standards
- HVAC system design and terminology
- Construction document interpretation
- Material properties and applications
- Cost estimation and pricing strategies
- Industry best practices and building codes

Your goal is to help users create accurate, professional insulation estimates efficiently.

## Your Capabilities

You have access to specialized tools for:

1. **Document Analysis**:
   - Extract project information from cover sheets
   - Analyze specification sections for insulation requirements
   - Extract measurements from mechanical drawings
   - Interpret drawing scales, schedules, and symbols

2. **Validation & Quality Control**:
   - Validate specifications against industry standards
   - Cross-reference specs with measurements
   - Identify missing or conflicting information
   - Recommend improvements and alternatives

3. **Calculation & Pricing**:
   - Calculate material quantities with fitting allowances
   - Compute labor hours based on system complexity
   - Apply pricing with markup and contingency
   - Generate cost-effective alternatives

4. **Quote Generation**:
   - Create professional quote documents
   - Generate material lists for distributors
   - Format executive summaries
   - Export in multiple formats

## Your Workflow

1. **Understand**: Ask clarifying questions to understand the project scope and requirements
2. **Analyze**: Use tools to extract and analyze project data from documents
3. **Validate**: Cross-check data for consistency and completeness
4. **Calculate**: Compute accurate quantities, labor, and pricing
5. **Recommend**: Provide alternatives and optimization suggestions
6. **Deliver**: Generate professional quotes and documentation

## Best Practices

- **Be proactive**: Identify potential issues before they become problems
- **Ask questions**: When information is ambiguous or missing, ask the user
- **Explain your reasoning**: Help users understand your recommendations
- **Validate thoroughly**: Cross-reference all data sources
- **Provide alternatives**: Show cost-saving options when appropriate
- **Be professional**: Generate high-quality, presentation-ready deliverables

## Current Session State

- Project Info: {project_status}
- Specifications: {spec_count} items
- Measurements: {measurement_count} items
- Pricing: {pricing_status}
- Quote: {quote_status}

Remember: You're not just a calculator - you're a trusted advisor helping users create better estimates.
"""

    def _format_system_prompt(self) -> str:
        """Format system prompt with current session state."""
        return self.system_prompt.format(
            project_status="Loaded" if self.session_data["project_info"] else "Not loaded",
            spec_count=len(self.session_data["specifications"]),
            measurement_count=len(self.session_data["measurements"]),
            pricing_status="Calculated" if self.session_data["pricing"] else "Not calculated",
            quote_status="Generated" if self.session_data["quote"] else "Not generated"
        )

    def add_file(self, file_path: str, file_type: str) -> str:
        """
        Add a file to the session for processing.

        Args:
            file_path: Path to the file
            file_type: Type of file ('spec', 'drawing', 'pricebook')

        Returns:
            File identifier
        """
        file_id = f"{file_type}_{len(self.session_data['uploaded_files']) + 1}"
        self.session_data["uploaded_files"][file_id] = {
            "path": file_path,
            "type": file_type,
            "uploaded_at": datetime.now().isoformat()
        }
        logger.info(f"Added file: {file_id} -> {file_path}")
        return file_id

    def run(
        self,
        user_message: str,
        context: Optional[Dict] = None,
        max_iterations: int = 10
    ) -> str:
        """
        Run the agent with a user message.

        This is the main agent loop that:
        1. Accepts user input
        2. Decides which tools to use
        3. Executes tools
        4. Processes results
        5. Returns response to user

        Args:
            user_message: User's message or question
            context: Optional context dictionary (uploaded files, etc.)
            max_iterations: Maximum tool use iterations to prevent infinite loops

        Returns:
            Agent's response message
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Add context information if provided
        if context:
            # Update session data with any new files
            if "spec_pdf" in context and context["spec_pdf"]:
                self.add_file(context["spec_pdf"], "spec")
            if "drawing_pdf" in context and context["drawing_pdf"]:
                self.add_file(context["drawing_pdf"], "drawing")
            if "pricebook" in context and context["pricebook"]:
                self.add_file(context["pricebook"], "pricebook")

        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Agent iteration {iteration}/{max_iterations}")

            try:
                # Call Claude with tool use capability
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    system=self._format_system_prompt(),
                    tools=self.tool_schemas,
                    messages=self.conversation_history
                )

                logger.info(f"Claude response stop_reason: {response.stop_reason}")

                # Check stop reason
                if response.stop_reason == "end_turn":
                    # Agent is done - extract final message
                    assistant_message = self._extract_text_content(response.content)

                    # Add to history
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": response.content
                    })

                    logger.info("Agent completed successfully")
                    return assistant_message

                elif response.stop_reason == "tool_use":
                    # Agent wants to use tools
                    logger.info("Agent requesting tool use")

                    # Process tool uses
                    tool_results = self._execute_tools(response.content)

                    # Add assistant's message to history
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": response.content
                    })

                    # Add tool results to history
                    self.conversation_history.append({
                        "role": "user",
                        "content": tool_results
                    })

                    # Continue loop - Claude will process tool results

                elif response.stop_reason == "max_tokens":
                    # Hit token limit - return partial response
                    assistant_message = self._extract_text_content(response.content)
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": response.content
                    })
                    logger.warning("Response truncated due to max_tokens")
                    return assistant_message + "\n\n[Response truncated - continue conversation for more details]"

                else:
                    # Unexpected stop reason
                    logger.error(f"Unexpected stop_reason: {response.stop_reason}")
                    return f"Unexpected response from agent (stop_reason: {response.stop_reason})"

            except Exception as e:
                logger.error(f"Error in agent loop: {e}", exc_info=True)
                return f"I encountered an error: {str(e)}\n\nPlease try rephrasing your request or contact support."

        # Max iterations reached
        logger.warning(f"Max iterations ({max_iterations}) reached")
        return "I've been working on this for a while. Let me summarize what I've found so far...\n\n" + \
               self._get_session_summary()

    def _extract_text_content(self, content_blocks: List) -> str:
        """Extract text from Claude response content blocks."""
        text_parts = []
        for block in content_blocks:
            if hasattr(block, "text"):
                text_parts.append(block.text)
        return "\n".join(text_parts)

    def _execute_tools(self, content_blocks: List) -> List[Dict]:
        """
        Execute tools requested by Claude.

        Args:
            content_blocks: Content blocks from Claude's response

        Returns:
            List of tool result dictionaries
        """
        tool_results = []

        for block in content_blocks:
            if block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input
                tool_use_id = block.id

                logger.info(f"🔧 Executing tool: {tool_name}")
                logger.debug(f"   Input: {json.dumps(tool_input, indent=2)}")

                try:
                    # Get tool handler
                    if tool_name not in self.tools:
                        raise ValueError(f"Unknown tool: {tool_name}")

                    tool_handler = self.tools[tool_name]

                    # Execute tool
                    result = tool_handler(**tool_input)

                    # Update session data based on tool results
                    self._update_session_data(tool_name, result)

                    # Create tool result
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": json.dumps(result, indent=2)
                    })

                    logger.info(f"   ✅ Tool succeeded")

                except Exception as e:
                    logger.error(f"   ❌ Tool failed: {e}", exc_info=True)

                    # Create error result
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": json.dumps({
                            "success": False,
                            "error": str(e),
                            "tool": tool_name
                        }),
                        "is_error": True
                    })

        return tool_results

    def _update_session_data(self, tool_name: str, result: Dict) -> None:
        """Update session data based on tool execution results."""
        if not result.get("success", False):
            return

        if tool_name == "extract_project_info":
            self.session_data["project_info"] = result.get("project_info")
            logger.info("Updated session: project_info")

        elif tool_name == "extract_specifications":
            self.session_data["specifications"] = result.get("specifications", [])
            logger.info(f"Updated session: {len(self.session_data['specifications'])} specifications")

        elif tool_name == "extract_measurements":
            self.session_data["measurements"] = result.get("measurements", [])
            logger.info(f"Updated session: {len(self.session_data['measurements'])} measurements")

        elif tool_name == "calculate_pricing":
            self.session_data["pricing"] = result
            logger.info(f"Updated session: pricing = ${result.get('total', 0):,.2f}")

        elif tool_name == "generate_quote":
            self.session_data["quote"] = result
            logger.info(f"Updated session: quote generated")

    def _get_session_summary(self) -> str:
        """Get summary of current session state."""
        summary_parts = ["Current Session State:", ""]

        # Project info
        if self.session_data["project_info"]:
            info = self.session_data["project_info"]
            summary_parts.append(f"Project: {info.get('project_name', 'N/A')}")
            summary_parts.append(f"Location: {info.get('location', 'N/A')}")
            summary_parts.append("")

        # Specifications
        spec_count = len(self.session_data["specifications"])
        summary_parts.append(f"Specifications: {spec_count} items")

        # Measurements
        measurement_count = len(self.session_data["measurements"])
        summary_parts.append(f"Measurements: {measurement_count} items")

        # Pricing
        if self.session_data["pricing"]:
            total = self.session_data["pricing"].get("total", 0)
            summary_parts.append(f"Estimated Total: ${total:,.2f}")

        # Quote
        if self.session_data["quote"]:
            summary_parts.append("Quote: Generated ✓")

        return "\n".join(summary_parts)

    def get_session_data(self) -> Dict[str, Any]:
        """Get current session data."""
        return self.session_data.copy()

    def reset_session(self) -> None:
        """Reset the session, clearing all data and conversation history."""
        self.conversation_history = []
        self.session_data = {
            "project_info": None,
            "specifications": [],
            "measurements": [],
            "pricing": None,
            "quote": None,
            "uploaded_files": {}
        }
        logger.info("Session reset")

    def export_session(self, output_path: str) -> None:
        """
        Export session data to JSON file.

        Args:
            output_path: Path to save JSON file
        """
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "model": self.model,
            "session_data": self.session_data,
            "message_count": len(self.conversation_history)
        }

        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Session exported to {output_path}")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_agent(api_key: Optional[str] = None) -> InsulationEstimationAgent:
    """
    Create a new estimation agent instance.

    Args:
        api_key: Optional API key (uses ANTHROPIC_API_KEY env var if not provided)

    Returns:
        InsulationEstimationAgent instance
    """
    return InsulationEstimationAgent(api_key=api_key)


def quick_estimate(
    spec_pdf: Optional[str] = None,
    drawing_pdf: Optional[str] = None,
    pricebook: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Quick estimation workflow - process PDFs and generate quote in one call.

    Args:
        spec_pdf: Path to specification PDF
        drawing_pdf: Path to drawing PDF
        pricebook: Path to pricebook file
        api_key: Anthropic API key

    Returns:
        Dictionary with quote and session data
    """
    agent = create_agent(api_key)

    # Build context
    context = {}
    if spec_pdf:
        context["spec_pdf"] = spec_pdf
    if drawing_pdf:
        context["drawing_pdf"] = drawing_pdf
    if pricebook:
        context["pricebook"] = pricebook

    # Run agent with comprehensive request
    message = """
    I've uploaded project documents. Please:
    1. Extract project information
    2. Analyze specifications
    3. Extract measurements from drawings
    4. Validate all data and cross-reference
    5. Calculate pricing
    6. Generate a complete quote

    Let me know if you find any issues or need clarification.
    """

    response = agent.run(message, context=context, max_iterations=15)

    return {
        "response": response,
        "session_data": agent.get_session_data(),
        "quote_ready": agent.session_data["quote"] is not None
    }


# ============================================================================
# CLI INTERFACE
# ============================================================================

def cli_main():
    """Command-line interface for the estimation agent."""
    import sys

    print("=" * 70)
    print("CLAUDE ESTIMATION AGENT - Interactive CLI")
    print("=" * 70)
    print()

    # Initialize agent
    try:
        agent = create_agent()
        print("✅ Agent initialized successfully")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        sys.exit(1)

    print("Commands:")
    print("  - Type your question or request")
    print("  - Type 'upload <path>' to add a file")
    print("  - Type 'status' to see session summary")
    print("  - Type 'export <path>' to save session data")
    print("  - Type 'reset' to start over")
    print("  - Type 'quit' to exit")
    print()

    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.lower() == "quit":
                print("Goodbye!")
                break

            elif user_input.lower() == "status":
                print()
                print(agent._get_session_summary())
                print()
                continue

            elif user_input.lower() == "reset":
                agent.reset_session()
                print("✅ Session reset")
                print()
                continue

            elif user_input.lower().startswith("export "):
                path = user_input.split(" ", 1)[1]
                agent.export_session(path)
                print(f"✅ Session exported to {path}")
                print()
                continue

            elif user_input.lower().startswith("upload "):
                path = user_input.split(" ", 1)[1]
                # Determine file type based on path or ask
                if "spec" in path.lower():
                    file_type = "spec"
                elif "draw" in path.lower():
                    file_type = "drawing"
                else:
                    file_type = input("File type (spec/drawing/pricebook): ").strip()

                file_id = agent.add_file(path, file_type)
                print(f"✅ Uploaded: {file_id}")
                print()
                continue

            # Regular message - send to agent
            print()
            print("Agent: ", end="", flush=True)

            response = agent.run(user_input)
            print(response)
            print()

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    cli_main()
