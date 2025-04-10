import pytest
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio
import json

# This will be imported after we create the implementation file
# from pseudoscribe.infrastructure.vault_sync import VaultSync

class TestVaultSync:
    """Test suite for the VaultSync class."""
    
    @pytest.fixture
    def temp_vault_dir(self):
        """Create a temporary directory to simulate an Obsidian vault."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_files(self, temp_vault_dir):
        """Create sample markdown files in the temporary vault directory."""
        # Create a few sample markdown files
        files = []
        
        # Create a simple note
        note1_path = os.path.join(temp_vault_dir, "note1.md")
        with open(note1_path, "w") as f:
            f.write("# Note 1\n\nThis is a simple note.")
        files.append(note1_path)
        
        # Create a note with links
        note2_path = os.path.join(temp_vault_dir, "note2.md")
        with open(note2_path, "w") as f:
            f.write("# Note 2\n\nThis note links to [[note1]].")
        files.append(note2_path)
        
        # Create a note in a subfolder
        subfolder_path = os.path.join(temp_vault_dir, "subfolder")
        os.makedirs(subfolder_path, exist_ok=True)
        note3_path = os.path.join(subfolder_path, "note3.md")
        with open(note3_path, "w") as f:
            f.write("# Note 3\n\nThis note is in a subfolder and links to [[../note1]].")
        files.append(note3_path)
        
        return files
    
    @pytest.fixture
    def vault_sync(self, temp_vault_dir):
        """Create a VaultSync instance for testing."""
        from pseudoscribe.infrastructure.vault_sync import VaultSync
        return VaultSync(vault_path=temp_vault_dir)
    
    @pytest.mark.asyncio
    async def test_initialize_vault(self, temp_vault_dir):
        """Test that initialize_vault creates the necessary files and directories."""
        from pseudoscribe.infrastructure.vault_sync import VaultSync
        
        # Create a VaultSync instance with a non-existent vault path
        new_vault_path = os.path.join(temp_vault_dir, "new_vault")
        vault_sync = VaultSync(vault_path=new_vault_path)
        
        # Initialize the vault
        await vault_sync.initialize_vault()
        
        # Check that the vault directory was created
        assert os.path.exists(new_vault_path)
        assert os.path.isdir(new_vault_path)
        
        # Check that the .obsidian directory was created
        obsidian_dir = os.path.join(new_vault_path, ".obsidian")
        assert os.path.exists(obsidian_dir)
        assert os.path.isdir(obsidian_dir)
        
        # Check that the config.json file was created
        config_path = os.path.join(obsidian_dir, "app.json")
        assert os.path.exists(config_path)
        
        # Check that the config file contains valid JSON
        with open(config_path, "r") as f:
            config = json.load(f)
            assert isinstance(config, dict)
    
    @pytest.mark.asyncio
    async def test_scan_vault(self, vault_sync, sample_files):
        """Test that scan_vault correctly identifies all markdown files in the vault."""
        # Scan the vault
        files = await vault_sync.scan_vault()
        
        # Check that all sample files were found
        for sample_file in sample_files:
            assert any(Path(sample_file).resolve() == Path(file).resolve() for file in files)
        
        # Check that only markdown files were found
        for file in files:
            assert file.endswith(".md")
    
    @pytest.mark.asyncio
    async def test_read_note(self, vault_sync, sample_files):
        """Test that read_note correctly reads the content of a note."""
        # Read the first note
        note_path = sample_files[0]
        note_content = await vault_sync.read_note(note_path)
        
        # Check that the content matches the expected content
        with open(note_path, "r") as f:
            expected_content = f.read()
        assert note_content == expected_content
    
    @pytest.mark.asyncio
    async def test_write_note(self, vault_sync, temp_vault_dir):
        """Test that write_note correctly writes content to a note."""
        # Create a new note path
        note_path = os.path.join(temp_vault_dir, "new_note.md")
        
        # Write content to the note
        note_content = "# New Note\n\nThis is a new note created by the test."
        await vault_sync.write_note(note_path, note_content)
        
        # Check that the note was created
        assert os.path.exists(note_path)
        
        # Check that the content matches the expected content
        with open(note_path, "r") as f:
            actual_content = f.read()
        assert actual_content == note_content
    
    @pytest.mark.asyncio
    async def test_extract_links(self, vault_sync, sample_files):
        """Test that extract_links correctly identifies all links in a note."""
        # Extract links from the second note (which contains a link)
        note_path = sample_files[1]
        links = await vault_sync.extract_links(note_path)
        
        # Check that the expected link was found
        assert "note1" in links
    
    @pytest.mark.asyncio
    async def test_build_graph(self, vault_sync, sample_files):
        """Test that build_graph correctly builds a graph of notes and their links."""
        # Build the graph
        graph = await vault_sync.build_graph()
        
        # Check that all sample files are in the graph
        for sample_file in sample_files:
            relative_path = os.path.relpath(sample_file, vault_sync.vault_path)
            assert relative_path in graph
        
        # Check that the links are correct
        note2_relative = os.path.relpath(sample_files[1], vault_sync.vault_path)
        assert "note1" in graph[note2_relative]["links"]
    
    @pytest.mark.asyncio
    async def test_sync_changes(self, vault_sync, sample_files, temp_vault_dir):
        """Test that sync_changes correctly identifies and syncs changes."""
        # First, scan the vault to build the initial cache
        await vault_sync.scan_vault()
        
        # Read all notes to populate the cache
        for file_path in sample_files:
            await vault_sync.read_note(file_path)
        
        # Simulate external changes by directly modifying a file
        note_path = sample_files[0]
        with open(note_path, "r", encoding="utf-8") as f:
            original_content = f.read()
        
        new_content = original_content + "\n\nThis is an added line."
        with open(note_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        
        # Create a new note directly (simulating external creation)
        new_note_path = os.path.join(temp_vault_dir, "new_note.md")
        new_note_content = "# New Note\n\nThis is a new note."
        with open(new_note_path, "w", encoding="utf-8") as f:
            f.write(new_note_content)
        
        # Sync changes
        changes = await vault_sync.sync_changes()
        
        # Check that the changes include the modified note and the new note
        assert len(changes["modified"]) == 1
        assert len(changes["added"]) == 1
        assert len(changes["deleted"]) == 0
        
        assert os.path.relpath(note_path, vault_sync.vault_path) in changes["modified"]
        assert os.path.relpath(new_note_path, vault_sync.vault_path) in changes["added"]
