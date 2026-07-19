import pytest
from multicliswarm.patching import apply_patch, ReplaceBlock

def test_apply_patch_exact_match():
    original = "def foo():\n    print('old')\n"
    blocks = [ReplaceBlock(search="    print('old')", replace="    print('new')")]
    
    patched = apply_patch(original, blocks)
    assert "print('new')" in patched
    assert "print('old')" not in patched

def test_apply_patch_stripped_match():
    original = "def foo():\n    print('old')\n"
    # Search block has extra whitespace that won't match exactly, but stripped will match
    blocks = [ReplaceBlock(search="\n    print('old')\n", replace="    print('new')")]
    
    patched = apply_patch(original, blocks)
    assert "print('new')" in patched

def test_apply_patch_not_found():
    original = "def foo():\n    print('old')\n"
    blocks = [ReplaceBlock(search="print('missing')", replace="print('new')")]
    
    with pytest.raises(ValueError, match="not found in the code"):
        apply_patch(original, blocks)

def test_apply_patch_ambiguous():
    original = "print('old')\nprint('old')\n"
    blocks = [ReplaceBlock(search="print('old')", replace="print('new')")]
    
    with pytest.raises(ValueError, match="is ambiguous"):
        apply_patch(original, blocks)
