from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "scripts" / "audit_report.py"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def build_fixture(path: Path, *, picture_single: bool = True) -> None:
    styles = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{W_NS}">
  <w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/></w:style>
  <w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/></w:style>
  <w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/></w:style>
</w:styles>"""
    spacing = '<w:spacing w:line="240" w:lineRule="auto"/>' if picture_single else ""
    document = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W_NS}">
  <w:body>
    <w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Chapter 1</w:t></w:r></w:p>
    <w:p><w:pPr><w:pStyle w:val="Heading2"/></w:pPr><w:r><w:t>1.1 Section</w:t></w:r></w:p>
    <w:p><w:pPr><w:pStyle w:val="Heading3"/></w:pPr><w:r><w:t>1.1.1 Subsection</w:t></w:r></w:p>
    <w:p><w:pPr>{spacing}</w:pPr><w:r><w:drawing/></w:r></w:p>
    <w:sectPr>
      <w:pgSz w:w="11906" w:h="16838"/>
      <w:pgMar w:top="1440" w:bottom="1440" w:left="1800" w:right="1800"/>
    </w:sectPr>
  </w:body>
</w:document>"""
    footer = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr xmlns:w="{W_NS}"><w:p><w:r><w:t>Example Organization</w:t></w:r></w:p></w:ftr>"""
    header = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:hdr xmlns:w="{W_NS}"><w:p/></w:hdr>"""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", document)
        archive.writestr("word/styles.xml", styles)
        archive.writestr("word/header1.xml", header)
        archive.writestr("word/footer1.xml", footer)


class AuditReportTests(unittest.TestCase):
    def run_audit(self, fixture: Path, level: int) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(AUDIT),
                str(fixture),
                "--max-heading-level",
                str(level),
                "--company",
                "Example Organization",
                "--page-size-twips",
                "11906,16838",
                "--margins-twips",
                "1440,1440,1800,1800",
            ],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_heading_three_is_allowed_when_configured(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "report.docx"
            build_fixture(fixture)
            result = self.run_audit(fixture, 3)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_heading_three_is_rejected_when_max_is_two(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "report.docx"
            build_fixture(fixture)
            result = self.run_audit(fixture, 2)
            self.assertEqual(result.returncode, 1)
            self.assertIn("标题3", result.stdout)

    def test_picture_spacing_is_checked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "report.docx"
            build_fixture(fixture, picture_single=False)
            result = self.run_audit(fixture, 3)
            self.assertEqual(result.returncode, 1)
            self.assertIn("图片段落", result.stdout)


if __name__ == "__main__":
    unittest.main()

