"""
context_loader — loads files from a context bundle directory for agent injection.

Usage:
    from tools.context_loader import load_context_bundle, BUNDLES

    bundle = load_context_bundle()                 # default LMS bundle
    bundle = load_context_bundle("cyber")          # cybersecurity bundle
"""

from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

BUNDLES: dict[str, dict] = {
    "lms": {
        "id": "lms",
        "label": "LMS Platform RFP",
        "description": "Learning Management System evaluation for multi-campus university",
        "dir": "context_bundles/lms",
    },
    "payroll": {
        "id": "payroll",
        "label": "Payroll Processing RFP",
        "description": "Full-service payroll processor evaluation for accuracy, compliance, and integration",
        "dir": "context_bundles/payroll",
    },
    "erp": {
        "id": "erp",
        "label": "Finance & HR Platform RFP",
        "description": "Enterprise ERP evaluation for financial management, HR, and payroll",
        "dir": "context_bundles/erp",
    },
}

DEFAULT_BUNDLE = "lms"


def load_context_bundle(bundle_id: str = DEFAULT_BUNDLE) -> dict[str, str]:
    """Read all .txt files from the specified bundle directory.

    Returns a dict keyed by file stem, e.g.:
        "policy"                → policy.txt
        "rfp_criteria_lms"      → rfp_criteria_lms.txt
        "scoring_rubric_cyber"  → scoring_rubric_cyber.txt

    Raises:
        KeyError: If bundle_id is not registered in BUNDLES.
        FileNotFoundError: If the bundle directory does not exist.
    """
    if bundle_id not in BUNDLES:
        raise KeyError(f"Unknown bundle '{bundle_id}'. Available: {list(BUNDLES)}")

    bundle_dir = BASE_DIR / "data" / BUNDLES[bundle_id]["dir"]
    if not bundle_dir.exists():
        raise FileNotFoundError(f"Bundle directory not found: {bundle_dir}")

    return {
        path.stem: path.read_text(encoding="utf-8")
        for path in sorted(bundle_dir.glob("*.txt"))
    }


def get_policy_path(bundle_id: str = DEFAULT_BUNDLE) -> Path:
    """Return the absolute path to policy.txt for the given bundle."""
    if bundle_id not in BUNDLES:
        raise KeyError(f"Unknown bundle '{bundle_id}'. Available: {list(BUNDLES)}")
    return BASE_DIR / "data" / BUNDLES[bundle_id]["dir"] / "policy.txt"
