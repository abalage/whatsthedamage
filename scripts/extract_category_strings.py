#!/usr/bin/env python3
"""
Generate a TypeScript file containing category display names wrapped in $gettext()
calls for translation extraction. This script is called during 'make lang'.

The generated file (frontend/src/js/categoryTranslations.ts) is used solely for
translation extraction - it is not used at runtime. Runtime category names
are fetched from the API.
"""

import sys
from pathlib import Path

# Add the src directory to path so we can import config
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from whatsthedamage.config.config import AVAILABLE_CATEGORIES

# Path to the output file
OUTPUT_FILE = Path(__file__).parent.parent / "frontend" / "src" / "js" / "categoryTranslations.ts"

# Generate the TypeScript content
content = """// Category display names for translation extraction.
// This file is auto-generated from backend config (whatsthedamage.config.config.AVAILABLE_CATEGORIES).
// DO NOT EDIT MANUALLY - edit the backend config and re-run 'make lang'.
// These strings are extracted by vue-gettext-extract for translation.
// Runtime category names are fetched from the API, not from this file.

// Declare $gettext for extraction (injected by vue3-gettext plugin at runtime)
declare const $gettext: (s: string) => string;

// Array of all category display names - used only for extraction
export const categoryTranslations = [
"""

# Add each category's default_name wrapped in $gettext()
for i, cat in enumerate(AVAILABLE_CATEGORIES):
    comma = "," if i < len(AVAILABLE_CATEGORIES) - 1 else ""
    content += f'  $gettext("{cat.default_name}"){comma}\n'

content += """\n];
"""

# Ensure the output directory exists
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

# Write the file
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Generated {len(AVAILABLE_CATEGORIES)} category translations to {OUTPUT_FILE}")
