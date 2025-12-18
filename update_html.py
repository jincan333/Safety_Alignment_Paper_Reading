import re
import json
import os

def parse_readme(readme_path="README.md"):
    """
    Parses the README.md file to extract paper entries.
    Assumes the table starts with specific headers.
    """
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: {readme_path} not found.")
        return []

    # Find the table part
    # Look for the header row
    header_pattern = r"\|\s*Time\s*\|\s*Venue\s*\|\s*Paper\s*\|\s*Research Question/Idea\s*\|\s*Method\s*\|\s*Remark\s*\|\s*Bib\s*\|"
    match = re.search(header_pattern, content, re.IGNORECASE)
    
    if not match:
        print("Error: Could not find the table header in README.md")
        return []

    # Get the content after the header
    table_content = content[match.end():]
    
    # Process lines
    lines = table_content.strip().split('\n')
    data = []
    
    # Skip the separator line (e.g., | :--- | :--- | ...)
    start_idx = 0
    if lines[0].strip().startswith('|') and '---' in lines[0]:
        start_idx = 1

    for line in lines[start_idx:]:
        line = line.strip()
        if not line.startswith('|'):
            continue
            
        # Stop if we hit a line that isn't a table row (or end of file)
        # Simple heuristic: if it doesn't look like a table row, stop
        if not line.startswith('|'):
            break

        # Split columns
        # Note: Simple split by '|' might break if '|' is inside content (e.g. math or links)
        # A more robust regex split is safer, but assuming standard markdown table format for now
        # We use a regex that matches the pipe separators
        
        # Remove leading/trailing pipes
        if line.startswith('|'): line = line[1:]
        if line.endswith('|'): line = line[:-1]
        
        cols = [c.strip() for c in line.split('|')]
        
        # Check if we have enough columns (Time, Venue, Paper, Question, Method, Remark, Bib)
        # We need at least 6 columns for the HTML (Bib is usually not in the main HTML table or handled differently)
        if len(cols) >= 6:
            # Paper column often contains [Title](Link)
            # We want to convert Markdown link to HTML link
            paper_md = cols[2]
            paper_html = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', paper_md)
            
            # Method column often contains **bold**
            method_md = cols[4]
            # No need to process bold here since JS will handle it, or process it here?
            # The JS now handles it, but let's keep Python doing basic bold conversion if it sees it
            # But the user said "markdown symbols such as ** still cannot show correctly", implying the HTML content already has **
            # Let's check how we generate HTML.
            # Currently: method_html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', method_md)
            # This handles Method column.
            # But "Question" column might also have **.
            
            question_md = cols[3]
            # Convert bold in question too
            question_html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', question_md)
            
            # Re-convert method just in case
            method_html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', method_md)
            
            # Remark often contains latex colors $\color{green}{\checkmark}$
            # We keep it as is for MathJax to render, but you might want to process unicode emojis if any
            remark_md = cols[5]

            # Bib column
            bib_md = cols[6] if len(cols) > 6 else ""
            
            entry = {
                "time": cols[0],
                "venue": cols[1],
                "paper": paper_html,
                "question": question_html,
                "method": method_html,
                "remark": remark_md,
                "bib": bib_md
            }
            data.append(entry)
            
    return data

def update_index_html(data, html_path="index.html"):
    """
    Updates the index.html file with the new data.
    """
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
    except FileNotFoundError:
        print(f"Error: {html_path} not found.")
        return

    # Create the new JSON string
    new_data_json = json.dumps(data, indent=4)
    
    # Regex to find the data variable definition in the script tag
    # const data = [ ... ];
    pattern = r"(const\s+data\s*=\s*)\[[\s\S]*?\];"
    
    # Check if pattern exists
    if not re.search(pattern, html_content):
        print("Error: Could not find 'const data = [...]' in index.html")
        return

    # Escape backslashes in the new_data_json string before using it in re.sub
    # This prevents re.sub from interpreting \u sequences (common in unicode) as escape sequences
    new_data_json_escaped = new_data_json.replace('\\', '\\\\')

    # Replace the old data with new data
    new_html_content = re.sub(pattern, f"\\1{new_data_json_escaped};", html_content)
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(new_html_content)
    
    print(f"Successfully updated {html_path} with {len(data)} entries.")

if __name__ == "__main__":
    entries = parse_readme()
    if entries:
        update_index_html(entries)

