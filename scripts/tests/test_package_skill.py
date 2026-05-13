import zipfile
import pytest
from pathlib import Path
import sys

# Import package_skill from the parent directory
sys.path.insert(0, str(Path(__file__).parent.parent))
from package_skill import package_skill, validate_frontmatter

def test_validate_frontmatter_valid(tmp_path):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: my-skill\ndescription: A test skill\n---\nBody")
    
    fm = validate_frontmatter(skill_dir)
    assert fm["name"] == "my-skill"
    assert fm["description"] == "A test skill"

def test_validate_frontmatter_mismatch(tmp_path):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: wrong-name\ndescription: A test skill\n---\nBody")
    
    with pytest.raises(ValueError, match="does not match directory name"):
        validate_frontmatter(skill_dir)

def test_package_skill_creation(tmp_path):
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: test-skill\ndescription: desc\n---\nBody")
    
    # Create allowed directories and files
    (skill_dir / "references").mkdir()
    (skill_dir / "references" / "ref1.md").write_text("ref")
    
    (skill_dir / "scripts").mkdir()
    (skill_dir / "scripts" / "script1.py").write_text("print('hello')")
    
    # Create excluded directories and files
    (skill_dir / "scripts" / "tests").mkdir()
    (skill_dir / "scripts" / "tests" / "test_script.py").write_text("test")
    
    (skill_dir / "scripts" / "__pycache__").mkdir()
    (skill_dir / "scripts" / "__pycache__" / "script1.cpython-39.pyc").write_text("binary")
    
    (skill_dir / ".env").write_text("SECRET=1")
    (skill_dir / "some-other-file.txt").write_text("ignore me")
    
    out_dir = tmp_path / "out"
    
    zip_path = package_skill(str(skill_dir), output_dir=str(out_dir))
    
    assert zip_path.exists()
    
    with zipfile.ZipFile(zip_path, 'r') as zf:
        names = zf.namelist()
        # Should include
        assert "SKILL.md" in names
        assert "references/ref1.md" in names
        assert "scripts/script1.py" in names
        # Should NOT include
        assert "scripts/tests/test_script.py" not in names
        assert "scripts/__pycache__/script1.cpython-39.pyc" not in names
        assert ".env" not in names
        assert "some-other-file.txt" not in names
