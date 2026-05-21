from __future__ import annotations

import re

from tests.conftest import ROOT


FINDING_ID_PATTERN = re.compile(r'id="([^"]+)"')


def test_finding_catalog_documents_rule_ids():
    docs = (ROOT / "docs" / "findings.md").read_text(encoding="utf-8")
    rule_ids = {
        match.group(1)
        for path in (ROOT / "context_health" / "rules").glob("*.py")
        for match in FINDING_ID_PATTERN.finditer(path.read_text(encoding="utf-8"))
    }

    missing = sorted(finding_id for finding_id in rule_ids if f"`{finding_id}`" not in docs)

    assert not missing
