"""
VendorLens MCP tool server.

Exposes two tools via the official MCP Python SDK (stdio transport):

  document_reader(filename) — returns full text of a vendor proposal file
  policy_lookup(query)      — searches UMPO policy.txt for relevant rules

The underlying Python functions (_document_reader, _policy_lookup) are also
importable directly by agents for Day 2/3. Day 4 wires these into LangGraph
via the MCP adapter so the pipeline calls them through the MCP protocol.

Run standalone:
    cd backend
    python tools/mcp_server.py
"""

import re
from pathlib import Path

from mcp.server.fastmcp import FastMCP

BASE_DIR = Path(__file__).parent.parent
DOCS_DIR = BASE_DIR / "data" / "vendor_proposals"
POLICY_PATH = BASE_DIR / "data" / "context_bundle" / "policy.txt"


def make_policy_lookup(policy_path: Path):
    """Return a policy_lookup function bound to a specific policy file."""
    def _lookup(query: str) -> str:
        if not policy_path.exists():
            return f"ERROR: policy file not found at {policy_path}"
        policy_text = policy_path.read_text(encoding="utf-8")
        sections = [s.strip() for s in re.split(r"(?=SECTION \d+:)", policy_text) if s.strip()]
        query_words = {w.lower() for w in re.split(r"\W+", query) if len(w) > 2}
        scored = []
        for section in sections:
            hits = sum(1 for w in query_words if w in section.lower())
            if hits > 0:
                scored.append((hits, section))
        if not scored:
            return policy_text
        scored.sort(key=lambda x: x[0], reverse=True)
        return "\n\n".join(text for _, text in scored[:3])
    return _lookup

mcp = FastMCP("VendorLens Tools")


# ---------------------------------------------------------------------------
# Plain Python implementations (importable by agents without MCP overhead)
# ---------------------------------------------------------------------------

def _document_reader(filename: str) -> str:
    """Return full text of a proposal document from data/vendor_proposals/."""
    matches = list(DOCS_DIR.rglob(filename))
    if not matches:
        return f"ERROR: file not found: {filename}"
    return matches[0].read_text(encoding="utf-8")


def _policy_lookup(query: str) -> str:  # default bundle (LMS)
    """Search UMPO policy.txt for sections relevant to the query.

    Splits policy.txt by section headers and scores each section by
    keyword overlap with the query. Returns the top three matching
    sections. Falls back to the full policy text if nothing matches.
    """
    if not POLICY_PATH.exists():
        return f"ERROR: policy file not found at {POLICY_PATH}"

    policy_text = POLICY_PATH.read_text(encoding="utf-8")

    # Split on "SECTION N:" headers, keeping the header with its body
    sections = [s.strip() for s in re.split(r"(?=SECTION \d+:)", policy_text) if s.strip()]

    # Score sections by query keyword overlap
    query_words = {w.lower() for w in re.split(r"\W+", query) if len(w) > 2}
    scored = []
    for section in sections:
        section_lower = section.lower()
        hits = sum(1 for w in query_words if w in section_lower)
        if hits > 0:
            scored.append((hits, section))

    if not scored:
        return policy_text  # return everything if no keyword match

    scored.sort(key=lambda x: x[0], reverse=True)
    return "\n\n".join(text for _, text in scored[:3])


# ---------------------------------------------------------------------------
# MCP tool definitions (wraps the plain functions above)
# ---------------------------------------------------------------------------

@mcp.tool()
def document_reader(filename: str) -> str:
    """Return the full text of a vendor proposal document.

    Args:
        filename: The file name only, e.g. blackboard.txt
    """
    return _document_reader(filename)


@mcp.tool()
def policy_lookup(query: str) -> str:
    """Search UMPO procurement policy for rules matching the query.

    Args:
        query: A topic or question, e.g. "liability cap requirements"
    """
    return _policy_lookup(query)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
