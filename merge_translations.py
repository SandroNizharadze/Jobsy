#!/usr/bin/env python3
import os

# Read the additional translations
with open('additional_translations.txt', 'r', encoding='utf-8') as f:
    additional_content = f.read()

# Parse the additional translations into a dictionary
additional_translations = {}
current_msgid = None
current_msgstr = None

for line in additional_content.splitlines():
    if line.startswith('msgid '):
        if current_msgid is not None and current_msgstr is not None:
            additional_translations[current_msgid] = current_msgstr
        current_msgid = line
        current_msgstr = None
    elif line.startswith('msgstr '):
        current_msgstr = line
    elif not line.strip():
        # Empty line, process previous entry if available
        if current_msgid is not None and current_msgstr is not None:
            additional_translations[current_msgid] = current_msgstr
            current_msgid = None
            current_msgstr = None

# Add the last entry if there's any
if current_msgid is not None and current_msgstr is not None:
    additional_translations[current_msgid] = current_msgstr

# Read the existing translation file
with open('locale/en/LC_MESSAGES/django.po', 'r', encoding='utf-8') as f:
    existing_content = f.read()

# Backup the existing file
with open('locale/en/LC_MESSAGES/django.po.backup', 'w', encoding='utf-8') as f:
    f.write(existing_content)

# Find all existing msgids to avoid duplicates
existing_msgids = set()
for line in existing_content.splitlines():
    if line.startswith('msgid '):
        existing_msgids.add(line)

# Merge the translations
new_translations = ""
for msgid, msgstr in additional_translations.items():
    if msgid not in existing_msgids:
        new_translations += f"{msgid}\n{msgstr}\n\n"

# Append the new translations to the existing file
with open('locale/en/LC_MESSAGES/django.po', 'a', encoding='utf-8') as f:
    f.write("\n# Added new translations\n")
    f.write(new_translations)

print(f"Added {len(new_translations.splitlines()) // 3} new translations to the django.po file.") 