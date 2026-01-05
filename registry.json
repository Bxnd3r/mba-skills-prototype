import os
import json
import re

def create_registry():
    registry = []
    
    # Scan current directory for files ending in _audit.json
    for filename in os.listdir('.'):
        if filename.endswith('_audit.json') and filename != 'registry.json':
            
            # Create a pretty name from the filename
            # e.g., "new_york_university_stern_audit.json" -> "New York University Stern"
            name_slug = filename.replace('_audit.json', '')
            pretty_name = " ".join(word.capitalize() for word in name_slug.split('_'))
            
            # Generate a consistent color based on the name (hash)
            # This ensures the school always gets the same color on the chart
            hash_val = sum(ord(c) for c in pretty_name)
            r = (hash_val * 37) % 255
            g = (hash_val * 53) % 255
            b = (hash_val * 97) % 255
            color = f"rgba({r}, {g}, {b}, 1)"

            entry = {
                "id": name_slug,
                "name": pretty_name,
                "audit_file": filename,
                "color": color
            }
            registry.append(entry)

    # Save the master list
    with open('registry.json', 'w') as f:
        json.dump(registry, f, indent=2)
    print(f"✅ Registry updated with {len(registry)} schools.")

if __name__ == "__main__":
    create_registry()
