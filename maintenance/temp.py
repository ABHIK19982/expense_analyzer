import os
import re
from datetime import datetime


def add_responsive_css(css_content):
    """Add responsive design to existing CSS content"""

    # Base responsive CSS template
    responsive_template = """
/* Base responsive settings */
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

/* Responsive container */
.container {
    width: 100%;
    padding-right: 15px;
    padding-left: 15px;
    margin-right: auto;
    margin-left: auto;
}

/* Responsive images */
img {
    max-width: 100%;
    height: auto;
}

/* Responsive typography */
html {
    font-size: 16px;
}

/* Media Queries */
/* Mobile devices */
@media screen and (max-width: 480px) {
    html {
        font-size: 14px;
    }

    .container {
        width: 100%;
        padding: 10px;
    }
}

/* Tablets */
@media screen and (min-width: 481px) and (max-width: 768px) {
    .container {
        width: 95%;
        max-width: 720px;
    }
}

/* Small laptops */
@media screen and (min-width: 769px) and (max-width: 1024px) {
    .container {
        max-width: 960px;
    }
}

/* Desktops */
@media screen and (min-width: 1025px) {
    .container {
        max-width: 1200px;
    }
}

/* Flexbox grid system */
.row {
    display: flex;
    flex-wrap: wrap;
    margin-right: -15px;
    margin-left: -15px;
}

.col {
    flex: 1;
    padding: 0 15px;
}

/* Responsive utilities */
.hide-on-mobile {
    display: none;
}

@media screen and (min-width: 768px) {
    .hide-on-mobile {
        display: block;
    }
}

/* Smooth transitions */
* {
    transition: all 0.3s ease-in-out;
}
"""

    # Check if media queries already exist
    if '@media' not in css_content:
        # Add responsive template to existing CSS
        enhanced_css = css_content.strip() + "\n\n" + responsive_template

        # Add responsive properties to existing selectors
        enhanced_css = re.sub(
            r'({[^}]+})',
            lambda m: m.group(1).replace('}', '\n    max-width: 100%;\n}')
            if 'width' in m.group(1) and 'max-width' not in m.group(1)
            else m.group(1),
            enhanced_css
        )

        return enhanced_css
    return css_content


def process_css_files(static_folder):
    """Process all CSS files in the static folder and its subfolders"""
    modified_files = []

    for root, dirs, files in os.walk(static_folder):
        for file in files:
            if file.endswith('.css'):
                file_path = os.path.join(root, file)
                try:
                    # Read existing CSS content
                    with open(file_path, 'r', encoding='utf-8') as f:
                        original_content = f.read()

                    # Add responsive design
                    enhanced_content = add_responsive_css(original_content)

                    # Create backup of original file
                    backup_path = file_path + '.backup_' + datetime.now().strftime('%Y%m%d%H%M%S')
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        f.write(original_content)

                    # Write enhanced CSS
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(enhanced_content)

                    modified_files.append(file_path)
                    print(f"Successfully updated: {file_path}")

                except Exception as e:
                    print(f"Error processing {file_path}: {str(e)}")

    return modified_files


# Usage


if __name__ == "__main__":
    static_folder = "static"  # Adjust this path to your static folder location
    modified_files = process_css_files(static_folder)
    print(f"\nTotal files modified: {len(modified_files)}")
