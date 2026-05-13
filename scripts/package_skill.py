#!/usr/bin/env python3
import sys
import os
import zipfile
import re
from pathlib import Path
import yaml

def validate_frontmatter(skill_dir: Path) -> dict:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        raise FileNotFoundError(f"SKILL.md not found in {skill_dir}")
    
    content = skill_md.read_text(encoding='utf-8')
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        raise ValueError(f"No YAML frontmatter found in {skill_md}")
        
    try:
        fm = yaml.safe_load(match.group(1))
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML frontmatter: {e}")
        
    if not fm:
        raise ValueError("Empty YAML frontmatter")
        
    name = fm.get("name", "")
    if not name:
        raise ValueError("Missing 'name' in frontmatter")
    name = str(name).strip()
    if name != skill_dir.name:
        raise ValueError(f"Frontmatter name '{name}' does not match directory name '{skill_dir.name}'")
        
    desc = fm.get("description", "")
    if not desc:
        raise ValueError("Missing 'description' in frontmatter")
    if not str(desc).strip():
        raise ValueError("Empty 'description' in frontmatter")
        
    return fm

def package_skill(skill_path: str, output_dir: str = "skill-packages") -> Path:
    skill_dir = Path(skill_path).resolve()
    if not skill_dir.is_dir():
        raise NotADirectoryError(f"Skill directory not found: {skill_dir}")
        
    # Validate
    validate_frontmatter(skill_dir)
    
    # Create output dir (relative to current working directory unless absolute)
    out_dir_path = Path(output_dir).resolve()
    out_dir_path.mkdir(parents=True, exist_ok=True)
    
    out_zip = out_dir_path / f"{skill_dir.name}.skill"
    
    # Allowed top-level dirs/files
    allowed_top_level = {"SKILL.md", "references", "scripts", "assets"}
    
    with zipfile.ZipFile(out_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(skill_dir):
            rel_root = Path(root).relative_to(skill_dir)
            
            # Filter directories
            dirs[:] = [
                d for d in dirs 
                if d not in {".git", ".venv", "node_modules", "__pycache__", "tests", "fixtures"} 
                and not d.startswith(".")
            ]
            
            # Only include allowed top-level items
            if str(rel_root) == ".":
                dirs[:] = [d for d in dirs if d in allowed_top_level]
                
            for file in files:
                if file.startswith("."):
                    continue
                if file.endswith(".pyc"):
                    continue
                if str(rel_root) == "." and file not in allowed_top_level:
                    continue
                    
                file_path = Path(root) / file
                arcname = file_path.relative_to(skill_dir)
                zf.write(file_path, arcname)
                
    return out_zip

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python package_skill.py <skill_directory>")
        sys.exit(1)
    
    skill_path = sys.argv[1]
    
    # Ensure skill-packages is placed at repo root if running from anywhere
    repo_root = Path(__file__).parent.parent
    default_out_dir = repo_root / "skill-packages"
    
    try:
        out = package_skill(skill_path, output_dir=str(default_out_dir))
        print(f"Successfully packaged {Path(skill_path).name} into {out}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
