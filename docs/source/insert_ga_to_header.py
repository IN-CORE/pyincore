import os
from bs4 import BeautifulSoup

# Directory containing the built HTML files
build_dir = "docs/build"

# Google Analytics tracking ID
ga_key = os.environ.get("GA_KEY")

# Ensure GA_KEY is provided
if not ga_key:
    raise ValueError("Google Analytics tracking ID (GA_KEY) not provided.")

# Google Analytics code snippet to insert into the HTML files
ga_code = f"""
<!-- Global site tag (gtag.js) - Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id={ga_key}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{ga_key}');
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
