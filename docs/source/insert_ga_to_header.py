import os
from bs4 import BeautifulSoup

# Directory containing the built HTML files
build_dir = "docs/build"

# Google Analytics code snippet to insert into the HTML files
ga_code = f"""
        <script>
            // Fetch and execute the analytics script
            fetch('config/googleAnalytics.js')
            .then(response => response.text())
            .then(scriptContent => {{
                const scriptTag = document.createElement('script');
                scriptTag.textContent = scriptContent;
                document.head.appendChild(scriptTag);
            }})
            .catch(error => console.error('Failed to load analytics script:', error));
        </script>
"""

# Loop through each HTML file in the build directory
for filename in os.listdir(build_dir):
    if filename.endswith(".html"):
        filepath = os.path.join(build_dir, filename)
        print(f"Processing file: {filepath}")

        # Read the content of the HTML file
        with open(filepath, "r", encoding="utf-8") as file:
            html_content = file.read()

        # Parse HTML content using BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")

        # Find the <head> tag and insert the Google Analytics code before it
        head_tag = soup.find("head")
        if head_tag:
            print(f"Found <head> tag in {filename}:")
            print("Inserting Google Analytics code...")
            head_tag.insert(0, BeautifulSoup(ga_code, "html.parser"))

        # Write the modified HTML content back to the file
        with open(filepath, "w", encoding="utf-8") as file:
            file.write(str(soup))

print("Google Analytics code insertion completed.")
