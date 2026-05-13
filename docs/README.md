# Documentation Contributor Guide

This guide explains how to write and maintain articles in the `docs/` directory. Follow these conventions so that new pages look consistent and render correctly on the Jekyll site. The documentation site is English-only; Japanese support was removed on 2026-05-13.

---

## Table of Contents

- [Directory Structure](#directory-structure)
- [Page Types](#page-types)
- [YAML Frontmatter Reference](#yaml-frontmatter-reference)
- [Hand-Written Skill Guide (★) Template](#hand-written-skill-guide--template)
- [Auto-Generated Skill Guide Template](#auto-generated-skill-guide-template)
- [Styling Reference](#styling-reference)
- [Checklist: Adding a New Skill Guide](#checklist-adding-a-new-skill-guide)
- [Conventions and Pitfalls](#conventions-and-pitfalls)

---

## Directory Structure

```
docs/
├── _config.yml                  # Jekyll configuration (theme, callouts, search)
├── _includes/
│   └── nav_footer_custom.html   # Footer include
├── _sass/
│   └── custom/custom.scss       # Badge styles, hero, category cards
├── index.md                     # Root landing page
├── en/                          # English documentation
│   ├── index.md                 # EN top page (parent for all EN children)
│   ├── getting-started.md
    ├── skill-catalog.md         # Full catalog table (all skills)
    └── skills/
        ├── index.md             # Skill Guides index (★ legend, guide table)
        ├── vcp-screener.md      # Example: hand-written ★ guide
        └── sector-analyst.md    # Example: auto-generated guide
```

**Key points:**
- The published site is English-only. A previous `ja/` tree was removed on 2026-05-13.
- This README is for contributors on GitHub; it is not part of the published site navigation.

---

## Page Types

| Type | Location | Purpose |
|------|----------|---------|
| **Landing page** | `index.md` (root) | Redirect to English entry |
| **Top page** | `en/index.md` | Category cards, quick-start steps |
| **Getting Started** | `en/getting-started.md` | Installation, API setup, first-skill tutorial |
| **Skill Catalog** | `en/skill-catalog.md` | Full table of all skills with descriptions and API badges |
| **Skill Guide (★)** | `en/skills/<name>.md` | Hand-written 10-section detailed guide |
| **Skill Guide (auto)** | `en/skills/<name>.md` | Auto-generated from SKILL.md: overview, workflow, resources |

Hand-written guides are marked with ★ in `en/skills/index.md`.

---

## YAML Frontmatter Reference

Every page requires YAML frontmatter. Fields vary by page type.

### Skill Guide Frontmatter (en)

```yaml
---
layout: default
title: "Skill Name"          # Displayed in sidebar and browser tab
grand_parent: English        # Always "English" for en/ skill guides
parent: Skill Guides         # Always "Skill Guides" for en/ skill guides
nav_order: 44                # Position in sidebar (see numbering rules below)
permalink: /en/skills/skill-name/   # Explicit URL path
---
```

### Field Reference

| Field | Required | Description |
|-------|----------|-------------|
| `layout` | Yes | Always `default` |
| `title` | Yes | Page title. Use the English skill name |
| `grand_parent` | Yes (skills) | `English`. Omit for top-level pages |
| `parent` | Yes | `Skill Guides`. For top-level pages, use `English` |
| `nav_order` | Yes | Numeric sidebar position. See [nav_order numbering](#nav_order-numbering) |
| `permalink` | Yes | Explicit URL path (prevents Jekyll auto-generation) |
| `has_children` | Conditional | Set to `true` only on index pages that have child pages |
| `nav_exclude` | Conditional | Set to `true` to hide from sidebar (used on root `index.md`) |

---

## Hand-Written Skill Guide (★) Template

Hand-written guides use a 10-section structure. This is the gold standard for documentation quality.

### Section Structure

```markdown
# Skill Name
{: .no_toc }

One-sentence description of what the skill does.
{: .fs-6 .fw-300 }

[Download Skill Package (.skill)](https://github.com/xonevn-ai/xone-trading-skills/raw/main/skill-packages/<name>.skill){: .btn .btn-primary .fs-5 .mb-4 .mb-md-0 .mr-2 }
[View Source on GitHub](https://github.com/xonevn-ai/xone-trading-skills/tree/main/skills/<name>){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview
## 2. Prerequisites
## 3. Quick Start
## 4. How It Works
## 5. Usage Examples
## 6. Understanding the Output
## 7. Tips & Best Practices
## 8. Combining with Other Skills
## 9. Troubleshooting
## 10. Reference
```

### Section Guidelines

| Section | Content | Tips |
|---------|---------|------|
| **1. Overview** | What the skill does, what problem it solves, key features | Start with "what it solves" to hook the reader |
| **2. Prerequisites** | API keys, Python version, dependencies | Use `{: .api_required }` callout for API requirements |
| **3. Quick Start** | Minimal command to get first results | Include both CLI and natural-language prompt examples |
| **4. How It Works** | Internal pipeline, algorithm, phases | Use ASCII diagrams or numbered steps |
| **5. Usage Examples** | 4-6 real-world scenarios with prompts and expected output | Each example: Prompt → What happens → Why useful |
| **6. Understanding the Output** | Output file format, field definitions, rating tables | Use tables for score ranges and interpretations |
| **7. Tips & Best Practices** | Expert advice for getting the most value | Bullet list of actionable tips |
| **8. Combining with Other Skills** | Multi-skill workflows | Table format: Workflow name → Steps |
| **9. Troubleshooting** | Common errors and fixes | H3 per error scenario with Cause → Fix format |
| **10. Reference** | CLI arguments table, scoring component weights | Full table of all flags with defaults |

---

## Auto-Generated Skill Guide Template

Auto-generated guides are simpler and extracted from the skill's SKILL.md. They follow this structure:

```markdown
# Skill Name
{: .no_toc }

Description from SKILL.md frontmatter.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[Download Skill Package (.skill)](...){: .btn .btn-primary .fs-5 .mb-4 .mb-md-0 .mr-2 }
[View Source on GitHub](...){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview
## 2. When to Use
## 3. Prerequisites
## 4. Quick Start
## 5. Workflow
## 6. Resources
```

Auto-generated guides typically have 6 sections instead of 10. They lack the detailed examples, troubleshooting, and CLI reference found in ★ guides.

---

## Styling Reference

### API Badges

```markdown
<!-- Required API -->
<span class="badge badge-api">FMP Required</span>

<!-- Optional API -->
<span class="badge badge-optional">FINVIZ Optional</span>

<!-- No API needed -->
<span class="badge badge-free">No API</span>

<!-- Workflow skill -->
<span class="badge badge-workflow">Workflow</span>
```

### Callouts

Four callout types are defined in `_config.yml`:

```markdown
> This is a note.
{: .note }

> This is a warning.
{: .warning }

> This is a tip.
{: .tip }

> FMP API key is required.
{: .api_required }
```

### Buttons

```markdown
<!-- Primary button (blue) -->
[Label](url){: .btn .btn-primary .fs-5 .mb-4 .mb-md-0 .mr-2 }

<!-- Secondary button (outline) -->
[Label](url){: .btn .fs-5 .mb-4 .mb-md-0 }
```

### Table of Contents

Always use this exact pattern at the top of every page (after the subtitle):

```markdown
<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>
```


### Internal Links

Always use Liquid's `relative_url` filter for internal links:

```markdown
<!-- Link to another page -->
[FinViz Screener]({{ '/en/skills/finviz-screener/' | relative_url }})
```

Never hardcode absolute URLs for internal pages. The `relative_url` filter ensures correct paths regardless of the `baseurl` setting.

### External Links (GitHub)

```markdown
<!-- Download button -->
[Download Skill Package (.skill)](https://github.com/xonevn-ai/xone-trading-skills/raw/main/skill-packages/<name>.skill){: .btn .btn-primary .fs-5 .mb-4 .mb-md-0 .mr-2 }

<!-- Source link button -->
[View Source on GitHub](https://github.com/xonevn-ai/xone-trading-skills/tree/main/skills/<name>){: .btn .fs-5 .mb-4 .mb-md-0 }
```

### Code Blocks

Always specify the language for syntax highlighting:

````markdown
```bash
python3 skills/vcp-screener/scripts/screen_vcp.py --output-dir reports/
```

```python
import os
fmp_api_key = os.environ.get('FMP_API_KEY')
```

```yaml
---
layout: default
title: "Skill Name"
---
```
````

### Heading Exclusion

Use `{: .no_toc }` on the page title (H1) to exclude it from the auto-generated TOC:

```markdown
# Skill Name
{: .no_toc }
```

---

## Checklist: Adding a New Skill Guide

Follow these steps when adding a new skill guide page:

### 1. Create the English page

- [ ] Create `docs/en/skills/<skill-name>.md`
- [ ] File name: kebab-case, lowercase, matching the skill directory name
- [ ] Add YAML frontmatter (see [reference above](#skill-guide-frontmatter-en))
- [ ] Choose a `nav_order` number (see [numbering rules](#nav_order-numbering))
- [ ] Write content using the [★ template](#hand-written-skill-guide--template) or [auto template](#auto-generated-skill-guide-template)

### 2. Update index page

- [ ] Add the skill to `docs/en/skills/index.md` (Available Guides table)
  - Include ★ marker if hand-written
  - Include API badge

### 3. Update catalog page

- [ ] Add the skill to the appropriate category in `docs/en/skill-catalog.md`

### 4. Verify

- [ ] `permalink` paths match the file locations
- [ ] `nav_order` does not conflict with existing pages
- [ ] API badges are consistent across index, catalog, and guide pages
- [ ] All internal links use `{{ '...' | relative_url }}` syntax

---

## Conventions and Pitfalls

### nav_order Numbering

Current `nav_order` assignments for top-level en/ pages:

| nav_order | Page |
|-----------|------|
| 1 | Getting Started |
| 2 | Skill Catalog |
| 3 | Skill Guides (index) |

Skill guide pages use `nav_order` values from 1 to ~50. To avoid conflicts:
1. Check existing values in `docs/en/skills/` before assigning
2. Use the next available number

### File Naming

- Always use **kebab-case**: `vcp-screener.md`, not `VCP_Screener.md`
- The file name should match the skill directory name under `skills/`
- Never include spaces in file names

### Common Mistakes

| Mistake | Consequence | Fix |
|---------|-------------|-----|
| Missing `permalink` | Jekyll generates unexpected URL paths | Always set explicit `permalink` |
| Hardcoded internal URLs | Links break if `baseurl` changes | Use `{{ '...' | relative_url }}` |
| Forgetting to update index page | New guide is invisible in the guide listing | Update `en/skills/index.md` |
| Forgetting to update catalog | Skill missing from the catalog overview | Update `en/skill-catalog.md` |
| Using `{:toc}` without `{: .no_toc }` on H1 | Page title appears redundantly in TOC | Add `{: .no_toc }` after the H1 |
| Badge inconsistency | Confusing API requirement information | Keep badges identical across guide, index, and catalog |

### Content Language Rule

- All published documentation pages are in English. Skill titles also stay in English for searchability.

### Jekyll Build Notes

- This `docs/README.md` is visible on GitHub but will also be processed by Jekyll. It is not linked in the site navigation because it has no `parent` or `nav_order` frontmatter.
- Custom callout types (`warning`, `note`, `tip`, `api_required`) are defined in `_config.yml` under the `callouts` key.
- Custom badge CSS classes (`badge-free`, `badge-api`, `badge-optional`, `badge-workflow`) are defined in `_sass/custom/custom.scss`.
