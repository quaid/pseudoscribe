import os
import json
import re
import logging
import asyncio
from typing import Dict, List, Set, Optional, Any
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class VaultSync:
    """
    VaultSync provides functionality to interact with an Obsidian vault.
    
    This class provides methods to:
    1. Initialize a new vault
    2. Scan for markdown files
    3. Read and write notes
    4. Extract links between notes
    5. Build a knowledge graph
    6. Sync changes between the vault and the application
    
    The vault is expected to be a directory containing markdown files,
    potentially organized into subdirectories.
    """
    
    def __init__(self, vault_path: str):
        """
        Initialize the VaultSync with a path to an Obsidian vault.
        
        Args:
            vault_path: Path to the Obsidian vault directory
        """
        self.vault_path = vault_path
        self.last_sync_time = None
        self.file_cache = {}  # Cache of file contents to detect changes
        self.file_mtimes = {}  # Cache of file modification times
    
    async def initialize_vault(self) -> None:
        """
        Initialize a new Obsidian vault if it doesn't exist.
        
        Creates the vault directory and necessary subdirectories and config files.
        """
        logger.info(f"Initializing vault at {self.vault_path}")
        
        # Create the vault directory if it doesn't exist
        os.makedirs(self.vault_path, exist_ok=True)
        
        # Create the .obsidian directory
        obsidian_dir = os.path.join(self.vault_path, ".obsidian")
        os.makedirs(obsidian_dir, exist_ok=True)
        
        # Create a basic config file
        config_path = os.path.join(obsidian_dir, "app.json")
        if not os.path.exists(config_path):
            config = {
                "promptDelete": False,
                "alwaysUpdateLinks": True,
                "newLinkFormat": "shortest",
                "useMarkdownLinks": False,
                "attachmentFolderPath": "attachments",
                "userIgnoreFilters": [
                    "node_modules/",
                    ".git/"
                ]
            }
            
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
        
        logger.info(f"Vault initialized at {self.vault_path}")
    
    async def scan_vault(self) -> List[str]:
        """
        Scan the vault for markdown files.
        
        Returns:
            List of paths to markdown files in the vault
        """
        logger.info(f"Scanning vault at {self.vault_path}")
        
        markdown_files = []
        
        # Walk through the vault directory
        for root, dirs, files in os.walk(self.vault_path):
            # Skip .obsidian directory
            if ".obsidian" in dirs:
                dirs.remove(".obsidian")
            
            # Add markdown files to the list
            for file in files:
                if file.endswith(".md"):
                    file_path = os.path.join(root, file)
                    markdown_files.append(file_path)
        
        logger.info(f"Found {len(markdown_files)} markdown files in vault")
        return markdown_files
    
    async def read_note(self, note_path: str) -> str:
        """
        Read the content of a note.
        
        Args:
            note_path: Path to the note file
            
        Returns:
            Content of the note as a string
            
        Raises:
            FileNotFoundError: If the note doesn't exist
        """
        logger.debug(f"Reading note at {note_path}")
        
        if not os.path.exists(note_path):
            raise FileNotFoundError(f"Note not found: {note_path}")
        
        with open(note_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Cache the content for change detection
        self.file_cache[note_path] = content
        # Cache the modification time
        self.file_mtimes[note_path] = os.path.getmtime(note_path)
        
        return content
        
    async def _read_file_without_caching(self, file_path: str) -> str:
        """
        Read a file without updating the cache.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Content of the file as a string
            
        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return content
    
    async def write_note(self, note_path: str, content: str) -> None:
        """
        Write content to a note.
        
        Args:
            note_path: Path to the note file
            content: Content to write to the note
        """
        logger.debug(f"Writing note to {note_path}")
        
        # Create parent directories if they don't exist
        os.makedirs(os.path.dirname(os.path.abspath(note_path)), exist_ok=True)
        
        with open(note_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        # Update the cache
        self.file_cache[note_path] = content
        # Update the modification time
        self.file_mtimes[note_path] = os.path.getmtime(note_path)
    
    async def extract_links(self, note_path: str) -> Set[str]:
        """
        Extract links from a note.
        
        Args:
            note_path: Path to the note file
            
        Returns:
            Set of link targets found in the note
            
        Raises:
            FileNotFoundError: If the note doesn't exist
        """
        logger.debug(f"Extracting links from {note_path}")
        
        content = await self.read_note(note_path)
        
        # Extract wiki-style links [[link]]
        wiki_links = re.findall(r'\[\[(.*?)(?:\|.*?)?\]\]', content)
        
        # Extract markdown-style links [text](link)
        markdown_links = re.findall(r'\[.*?\]\((.*?)\)', content)
        
        # Combine all links
        all_links = set(wiki_links + markdown_links)
        
        # Clean up links (remove .md extension if present, etc.)
        cleaned_links = set()
        for link in all_links:
            # Remove .md extension
            if link.endswith(".md"):
                link = link[:-3]
            # Add to cleaned links
            cleaned_links.add(link)
        
        return cleaned_links
    
    async def build_graph(self) -> Dict[str, Dict[str, Any]]:
        """
        Build a graph of notes and their links.
        
        Returns:
            Dictionary mapping note paths to dictionaries containing metadata and links
        """
        logger.info(f"Building graph for vault at {self.vault_path}")
        
        graph = {}
        files = await self.scan_vault()
        
        # Process each file
        for file_path in files:
            relative_path = os.path.relpath(file_path, self.vault_path)
            
            # Extract metadata and links
            try:
                content = await self.read_note(file_path)
                links = await self.extract_links(file_path)
                
                # Extract title from content (first # heading)
                title_match = re.search(r'^#\s+(.*?)$', content, re.MULTILINE)
                title = title_match.group(1) if title_match else os.path.basename(file_path)
                
                # Add to graph
                graph[relative_path] = {
                    "title": title,
                    "path": relative_path,
                    "links": links,
                    "last_modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                }
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
        
        # Resolve links to actual file paths
        for note_path, note_data in graph.items():
            resolved_links = set()
            for link in note_data["links"]:
                # Handle relative links
                if link.startswith("../") or link.startswith("./"):
                    base_dir = os.path.dirname(note_path)
                    resolved_path = os.path.normpath(os.path.join(base_dir, link))
                else:
                    # Try to find a matching file
                    resolved_path = None
                    for path in graph.keys():
                        if path.endswith(f"{link}.md") or path == f"{link}.md":
                            resolved_path = path
                            break
                
                if resolved_path:
                    resolved_links.add(resolved_path)
            
            note_data["resolved_links"] = resolved_links
        
        logger.info(f"Built graph with {len(graph)} nodes")
        return graph
    
    async def sync_changes(self) -> Dict[str, List[str]]:
        """
        Identify and sync changes in the vault.
        
        Returns:
            Dictionary with lists of added, modified, and deleted files
        """
        logger.info(f"Syncing changes for vault at {self.vault_path}")
        
        changes = {
            "added": [],
            "modified": [],
            "deleted": []
        }
        
        # Get current files
        current_files = await self.scan_vault()
        current_files_set = set(current_files)
        
        # Check for deleted files
        if self.file_cache:
            cached_files_set = set(self.file_cache.keys())
            deleted_files = cached_files_set - current_files_set
            for file_path in deleted_files:
                relative_path = os.path.relpath(file_path, self.vault_path)
                changes["deleted"].append(relative_path)
                # Remove from cache
                del self.file_cache[file_path]
                if file_path in self.file_mtimes:
                    del self.file_mtimes[file_path]
        
        # Check for added and modified files
        for file_path in current_files:
            relative_path = os.path.relpath(file_path, self.vault_path)
            
            # Check if it's a new file
            if file_path not in self.file_cache:
                content = await self._read_file_without_caching(file_path)
                self.file_cache[file_path] = content
                self.file_mtimes[file_path] = os.path.getmtime(file_path)
                changes["added"].append(relative_path)
                continue
            
            # For existing files, read current content and compare with cached content
            current_content = await self._read_file_without_caching(file_path)
            cached_content = self.file_cache.get(file_path, "")
            
            # If content has changed, mark as modified
            if current_content != cached_content:
                self.file_cache[file_path] = current_content
                self.file_mtimes[file_path] = os.path.getmtime(file_path)
                changes["modified"].append(relative_path)
                continue
            
            # As a fallback, check modification time
            current_mtime = os.path.getmtime(file_path)
            if file_path not in self.file_mtimes or current_mtime > self.file_mtimes[file_path]:
                self.file_mtimes[file_path] = current_mtime
                changes["modified"].append(relative_path)
        
        # Update last sync time
        self.last_sync_time = datetime.now()
        
        logger.info(f"Sync completed: {len(changes['added'])} added, "
                   f"{len(changes['modified'])} modified, "
                   f"{len(changes['deleted'])} deleted")
        
        return changes
