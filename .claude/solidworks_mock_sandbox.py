"""
Simplified MCP Mock Server for Sandbox Testing
Uses mcp.server.fastmcp instead of external fastmcp package
"""
import json
import logging
import asyncio
from typing import Any, Dict, List
from datetime import datetime

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

mcp = FastMCP("solidworks_mock")


# =============================================================================
# ASSEMBLY STRUCTURE TOOL
# =============================================================================

@mcp.tool()
def solidworks_assembly_structure_tool(input: str) -> dict:
    """Send the assembly structure"""
    logger.info(f"Received assembly structure: {input[:200]}...")
    print(f"\n{'='*80}")
    print(f"MCP TOOL INVOKED - SOLIDWORKS ASSEMBLY STRUCTURE")
    print(f"{'='*80}")

    try:
        structure_data = json.loads(input)
        print(f"\nReceived Structure Data:")
        print(json.dumps(structure_data, indent=2))
    except json.JSONDecodeError:
        print(f"\nReceived Raw Input:")
        print(input)

    print(f"\n{'='*80}\n")
    return {"status": "received", "message": "Assembly structure processed"}


# =============================================================================
# WHAT'S WRONG ANALYSIS TOOL
# =============================================================================

MOCK_ERROR_DATA: List[Dict[str, Any]] = [
    {
        "error_id": "ERR-001",
        "type": "missing_reference",
        "severity": "high",
        "component": "Bracket-1",
        "description": "Referenced file not found: C:\\Projects\\Parts\\Bracket.sldprt",
        "suggested_fix": "Locate and relink the missing file or suppress the component"
    },
    {
        "error_id": "ERR-002",
        "type": "mate_conflict",
        "severity": "medium",
        "component": "Housing-2",
        "description": "Over-defined mates detected: Coincident1 conflicts with Distance1",
        "suggested_fix": "Delete or modify one of the conflicting mates"
    },
    {
        "error_id": "ERR-003",
        "type": "rebuild_error",
        "severity": "high",
        "component": "Shaft-1",
        "description": "Feature 'Cut-Extrude1' failed to rebuild: Sketch contains zero-length edges",
        "suggested_fix": "Edit the sketch and remove zero-length geometry"
    }
]


@mcp.tool()
def solidworks_whats_wrong_tool(input: str) -> str:
    """What's Wrong Analysis MCP tool - retrieves model errors/issues"""
    logger.info(f"Received whatswrong MCP request: {input[:200]}...")
    print(f"\n{'='*80}")
    print(f"MCP TOOL INVOKED - SOLIDWORKS WHAT'S WRONG ANALYSIS")
    print(f"{'='*80}")

    response = {
        "status": "success",
        "total_errors": len(MOCK_ERROR_DATA),
        "errors": MOCK_ERROR_DATA,
        "summary": {
            "high_severity": sum(1 for e in MOCK_ERROR_DATA if e.get("severity") == "high"),
            "medium_severity": sum(1 for e in MOCK_ERROR_DATA if e.get("severity") == "medium"),
            "low_severity": sum(1 for e in MOCK_ERROR_DATA if e.get("severity") == "low")
        },
        "model_path": "C:\\Users\\CADUser\\Documents\\Projects\\Assembly1.sldasm",
        "analysis_timestamp": datetime.now().isoformat()
    }

    print(f"\nReturning {len(MOCK_ERROR_DATA)} errors:")
    print(json.dumps(response, indent=2))
    print(f"{'='*80}\n")

    return json.dumps(response)


# =============================================================================
# DRAWING GENERATION TOOL
# =============================================================================

MOCK_DRAWING_STATE: Dict[str, Any] = {
    "default_template_path": "C:\\ProgramData\\SOLIDWORKS\\templates\\drawing.drwdot",
    "opened_model_path": "C:\\Users\\CADUser\\Documents\\Projects\\Assembly1.sldasm",
}


@mcp.tool()
def solidworks_dwggen_mcp_tool(input: str) -> str:
    """Drawing Generation MCP tool"""
    logger.info(f"Received dwggen MCP request: {input[:200]}...")
    print(f"\n{'='*80}")
    print(f"MCP TOOL INVOKED - SOLIDWORKS DRAWING GENERATOR")
    print(f"{'='*80}")

    try:
        task_data = json.loads(input)
        action = task_data.get("task_Type", "unknown")
        request_id = task_data.get("request_id", "unknown")

        print(f"\nRequest ID: {request_id}")
        print(f"Action: {action}")

        if action == "GetDefaultTemplatePath":
            return MOCK_DRAWING_STATE["default_template_path"]
        elif action == "GetOpenedModelPath":
            return MOCK_DRAWING_STATE["opened_model_path"]
        elif action in ["GeneratePreview", "GenerateDrawing", "OpenDrawing"]:
            return "success"
        else:
            return json.dumps({"status": "error", "message": f"Unknown action: {action}"})

    except json.JSONDecodeError as e:
        return json.dumps({"status": "error", "message": f"Invalid JSON: {str(e)}"})


if __name__ == "__main__":
    print("Starting MCP Mock Server on stdio...")
    print("Tools registered: solidworks_assembly_structure_tool, solidworks_whats_wrong_tool, solidworks_dwggen_mcp_tool")
    mcp.run()
