# Format profile

Create a task-specific profile before editing. Do not assume that every report uses the same institution, logo, footer, fonts, or heading depth.

## Required profile fields

| Field | Example | Notes |
|---|---|---|
| `template_path` | `/path/reference-template.docx` | Supplied by the user or workspace |
| `max_heading_level` | `3` | Highest body heading style |
| `toc_level` | `2` | Deepest heading shown in TOC |
| `page_size` | `A4 portrait` | Derive from template |
| `margins_twips` | `1440,1440,1800,1800` | Top, bottom, left, right |
| `header_image_policy` | `remove` | `keep` or `remove` |
| `footer_text` | `Example Organization` | Empty means no required text audit |
| `picture_line_spacing` | `single` | Apply to pictures in body and table cells |
| `output_name` | `report.docx` | Never overwrite the source |

## Heading decisions

Choose headings by meaning and scope, then apply numbering conventions. For example, if `max_heading_level=3`, a semantic `2.1.1` section uses Heading 3. If `max_heading_level=2`, that same lower-level item becomes a body paragraph unless the user asks to restructure it.

The TOC may be shallower than the body. Record `toc_level` separately and regenerate the TOC from real heading styles.

## Pictures, tables, and captions

- Apply picture spacing to every picture paragraph, including pictures nested in table cells.
- Avoid resampling source media unless the user requests compression.
- Put table captions above tables and figure captions below figures unless the template says otherwise.
- Keep captions with their objects when practical.
- Check baked-in caption text inside raster images. If it conflicts with the document numbering, crop only the obsolete caption region and add an editable caption without altering the technical image content.

## Visual QA

Structure checks do not replace rendering. Inspect every rendered page for font substitution, clipping, overlap, table row breaks, stale TOC pages, and inconsistent headers or footers. If one renderer lacks the required fonts, verify with Word, Pages, or another environment that has them.

