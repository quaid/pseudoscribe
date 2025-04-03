#!/usr/bin/env python3
import json
import os
from github import Github
from typing import Dict, List

def load_backlog(file_path: str) -> Dict:
    """Load the AGILE_BACKLOG.json file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def create_epic_label(g, repo, epic_name: str, color: str = "0366d6"):
    """Create a label for the epic if it doesn't exist."""
    try:
        return repo.create_label(epic_name, color)
    except:
        return repo.get_label(epic_name)

def format_issue_body(story: Dict, epic_value_statement: str) -> str:
    """Format the issue body with all relevant information."""
    body = [f"## Epic Value Statement\n{epic_value_statement}\n"]
    
    # Add points and type
    body.append(f"**Points:** {story.get('points', 'N/A')}")
    body.append(f"**Type:** {story.get('type', 'Feature')}")
    body.append(f"**Branch:** {story.get('branch', 'TBD')}\n")
    
    # Add BDD Scenarios if they exist
    if 'bddScenarios' in story:
        body.append("## BDD Scenarios")
        for scenario in story['bddScenarios']:
            body.append(f"\n### Feature: {scenario['feature']}")
            for scene in scenario['scenarios']:
                body.append(f"\n**Scenario:** {scene['name']}")
                body.append(f"- Given {scene['given']}")
                body.append(f"- When {scene['when']}")
                body.append(f"- Then {scene['then']}")
                if 'and' in scene:
                    body.append(f"- And {scene['and']}")
    
    # Add Acceptance Criteria if they exist
    if 'acceptanceCriteria' in story:
        body.append("\n## Acceptance Criteria")
        for criteria in story['acceptanceCriteria']:
            body.append(f"- {criteria}")
    
    # Add Test Strategy if it exists
    if 'testStrategy' in story:
        body.append("\n## Test Strategy")
        for test in story['testStrategy']:
            body.append(f"- {test}")
    
    return "\n".join(body)

def create_issues(token: str, repo_name: str, backlog_file: str):
    """Create GitHub issues from the backlog file."""
    g = Github(token)
    repo = g.get_repo(repo_name)
    backlog = load_backlog(backlog_file)
    
    print(f"Creating issues for project: {backlog['project']}")
    
    # Create issues for each epic and its stories
    for epic in backlog['epics']:
        epic_label = create_epic_label(g, repo, f"Epic: {epic['name']}")
        print(f"\nProcessing Epic: {epic['name']}")
        
        # Create issues for each story in the epic
        for story in epic['stories']:
            title = f"[{story['id']}] {story['name']}"
            body = format_issue_body(story, epic['valueStatement'])
            
            try:
                issue = repo.create_issue(
                    title=title,
                    body=body,
                    labels=[epic_label]
                )
                print(f"Created issue: {title}")
            except Exception as e:
                print(f"Error creating issue {title}: {str(e)}")

def main():
    # Get GitHub token from environment variable
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print("Error: GITHUB_TOKEN environment variable not set")
        return
    
    # Get repository name from git remote or environment
    repo_name = os.getenv('GITHUB_REPOSITORY')
    if not repo_name:
        print("Error: GITHUB_REPOSITORY environment variable not set")
        print("Format should be: username/repository")
        return
    
    backlog_file = "AGILE_BACKLOG.json"
    create_issues(token, repo_name, backlog_file)

if __name__ == "__main__":
    main()
