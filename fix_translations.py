import re

# Read the template file (new) for headers
with open('locale/en/LC_MESSAGES/django.po', 'r', encoding='utf-8') as f:
    template_content = f.read()

# Get the header from the template
header_match = re.search(r'^(.*?)msgid \"\"', template_content, re.DOTALL)
header = header_match.group(1) if header_match else ''

# Read the old translation file (with translations)
with open('locale/en/LC_MESSAGES/django.po.bak', 'r', encoding='utf-8') as f:
    old_content = f.read()

# Extract entries (msgid/msgstr pairs) from old file
entries = []
processed_msgids = set()
pattern = re.compile(r'(#:.*?msgid \"(.*?)\".*?msgstr \"(.*?)\")', re.DOTALL)

for match in pattern.finditer(old_content):
    entry = match.group(1)
    msgid = match.group(2)
    
    # Skip duplicate entries
    if msgid in processed_msgids:
        continue
    
    processed_msgids.add(msgid)
    
    # Fix specific entry with issue
    if 'msgid \"ხშირად დასმული კითხვები\"' in entry and '#| msgid \"მსგავსი ვაკანსიები\"' in entry:
        entry = entry.replace('#| msgid \"მსგავსი ვაკანსიები\"', '')
    
    entries.append(entry)

# Create new content
new_content = header + 'msgid \"\"\nmsgstr \"\"\n\"Project-Id-Version: Jobsy 1.0\\n\"\n\"Report-Msgid-Bugs-To: \\n\"\n\"POT-Creation-Date: 2025-05-19 15:12+0000\\n\"\n\"PO-Revision-Date: 2023-05-20 12:00+0000\\n\"\n\"Last-Translator: \\n\"\n\"Language-Team: English\\n\"\n\"Language: en\\n\"\n\"MIME-Version: 1.0\\n\"\n\"Content-Type: text/plain; charset=UTF-8\\n\"\n\"Content-Transfer-Encoding: 8bit\\n\"\n\"Plural-Forms: nplurals=2; plural=(n != 1);\\n\"\n\n' + '\n\n'.join(entries)

# Write the new file
with open('locale/en/LC_MESSAGES/django.po', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Translation file has been fixed and saved!") 