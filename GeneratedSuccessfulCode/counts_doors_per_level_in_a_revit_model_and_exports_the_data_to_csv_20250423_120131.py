# Purpose: This script counts doors per level in a Revit model and exports the data to CSV.

﻿import clr
clr.AddReference('RevitAPI')
import Autodesk.Revit.DB as DB # Use namespace import
import System # Keep for System.Exception handling if needed, though less critical now

# Assume 'doc' is pre-defined and available

# Initialize dictionaries to store counts and level mappings
level_door_counts = {}
level_id_to_name = {}
unassigned_count = 0

# Collect all Levels and initialize counts
try:
    level_collector = DB.FilteredElementCollector(doc).OfClass(DB.Level).WhereElementIsNotElementType()
    for level in level_collector:
        # Check if it's actually a Level object (robustness)
        if isinstance(level, DB.Level):
            try:
                level_name = level.Name # Direct property access is standard
                if level_name not in level_door_counts: # Avoid overwriting if names clash (unlikely for levels)
                     level_door_counts[level_name] = 0 # Initialize count for all known levels
                level_id_to_name[level.Id] = level_name
            except Exception as e:
                # print("# Error processing level {}: {}".format(level.Id, e)) # Optional debug info
                pass # Skip levels that cause errors or have problematic names
except Exception as e:
    print("# Error collecting levels: {}".format(e))
    # Consider if script should terminate or continue without levels

# Collect all Door instances
try:
    door_collector = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Doors).WhereElementIsNotElementType()

    # Iterate through doors and count per level
    for door in door_collector:
        try:
            level_id = door.LevelId
            # Check if LevelId is valid and exists in our collected levels
            if level_id is not None and level_id != DB.ElementId.InvalidElementId and level_id in level_id_to_name:
                level_name = level_id_to_name[level_id]
                # Ensure the level name exists in the counts dictionary (it should, based on above loop)
                if level_name in level_door_counts:
                     level_door_counts[level_name] += 1
                else:
                     # This case indicates a logic error or race condition if levels were modified
                     # Count as unassigned for robustness
                     unassigned_count += 1
            else:
                # Increment count for doors without a valid or found associated level
                unassigned_count += 1
        except AttributeError:
            # Handle rare cases where an element collected as a Door might lack .LevelId
             unassigned_count += 1
        except Exception as e:
            # print("# Error processing door {}: {}".format(door.Id, e)) # Optional debug info
            unassigned_count += 1 # Count as unassigned if any other error occurs during processing

except Exception as e:
     print("# Error collecting or processing doors: {}".format(e))
     # Script will continue and report counts gathered so far + unassigned

# Prepare CSV output
csv_lines = []
csv_lines.append('"Level Name","Door Count"') # CSV Header

# Add counts for levels, sorted alphabetically by level name
# Iterate through the initially collected levels to ensure all are listed, even with 0 count
sorted_level_names = sorted(level_door_counts.keys())
for level_name in sorted_level_names:
    count = level_door_counts.get(level_name, 0) # Get the final count using .get for safety
    # Escape double quotes within the level name for CSV format
    safe_level_name = '"' + level_name.replace('"', '""') + '"'
    csv_lines.append(','.join([safe_level_name, str(count)]))

# Add count for unassigned doors if any were found
if unassigned_count > 0:
    safe_unassigned_name = '"Unassigned/Level Not Found"'
    csv_lines.append(','.join([safe_unassigned_name, str(unassigned_count)]))

# Check if data was generated (at least header + one data row)
if len(csv_lines) > 1:
    file_content = "\n".join(csv_lines)
    # Print the export marker and data
    print("EXPORT::CSV::door_count_per_level.csv")
    print(file_content)
else:
    # This condition means no levels were found AND no doors were found/unassigned.
    if not level_id_to_name and unassigned_count == 0 : # Check if levels dictionary is empty
         print("# No Levels found in the project.")
    # This case should ideally not be reached if the primary check failed,
    # but serves as a fallback message.
    else:
         print("# No data generated for export. Check project for Levels and Doors.")