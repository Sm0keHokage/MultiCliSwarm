import pytest
import os
import tempfile
from multicliswarm.rag import get_codebase_context

def test_get_codebase_context():
    with tempfile.TemporaryDirectory() as tempdir:
        # Create a test file
        test_file = os.path.join(tempdir, "test.py")
        with open(test_file, "w") as f:
            f.write("def hello():\n    pass")
            
        # Create a .gitignore to test ignoring
        gitignore_file = os.path.join(tempdir, ".gitignore")
        with open(gitignore_file, "w") as f:
            f.write("ignored.py\n")
            
        ignored_file = os.path.join(tempdir, "ignored.py")
        with open(ignored_file, "w") as f:
            f.write("secret data")
            
        context = get_codebase_context(tempdir)
        
        assert "test.py" in context
        assert "def hello():" in context
        assert "ignored.py" not in context
        assert "secret data" not in context
