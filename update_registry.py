import os
import json

def create_registry():
    registry = []
    target_folder = 'raw_school_data'
    
    # Check if folder exists
    if os.path.exists(target_folder):
        # Scan the NEW folder
        for filename in os.listdir(target_folder):
            if filename.endswith('_curriculum.json'):
                
                # Clean up the name
                # "northwestern_university..._curriculum.json" -> "Northwestern University..."
                name_slug = filename.replace('_curriculum.json', '')
                pretty_name = " ".join(word.capitalize() for word in name_slug.split('_'))
                
                # Generate Color Hash
                hash_val = sum(ord(c) for c in pretty_name)
                r = (hash_val * 37) % 255
                g = (hash_val * 53) % 255
                b = (hash_val * 97) % 255
                color = f"rgba({r}, {g}, {b}, 1)"

                entry = {
                    "id": name_slug,
                    "name": pretty_name,
                    "audit_file": f"{target_folder}/{filename}", # Point to the correct path
                    "color": color
                }
                registry.append(entry)

    # Save registry in the ROOT (so index.html can find it easily)
    with open('registry.json', 'w') as f:
        json.dump(registry, f, indent=2)
    print(f"✅ Registry updated with {len(registry)} schools from {target_folder}.")

if __name__ == "__main__":
    create_registry()
