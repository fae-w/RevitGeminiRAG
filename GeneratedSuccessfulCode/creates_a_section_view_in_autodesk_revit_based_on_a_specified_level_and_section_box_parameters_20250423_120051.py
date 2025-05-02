# Purpose: This script creates a section view in Autodesk Revit based on a specified level and section box parameters.

﻿# Import necessary classes
import clr
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Level,
    ViewFamilyType,
    ViewSection,
    ElementId,
    ViewType,
    BoundingBoxXYZ,
    Transform,
    XYZ,
    BuiltInParameter
)

# --- Configuration ---
target_level_name = "L1 - Block 43"
# Arbitrary dimensions for the section box (in feet)
section_width = 50.0
section_height = 30.0 # Total vertical height
height_below_level = 5.0 # Portion of height below the level's elevation
section_depth_far = 20.0 # How far the view looks
section_depth_near = 0.0 # Distance from cut plane to near clip plane (usually 0)
# Section origin point (relative to project origin, X and Y can be adjusted)
section_origin_x = 0.0
section_origin_y = 0.0

# --- Helper Functions ---

def find_level_by_name(doc_param, level_name):
    """Finds a Level element by its exact name."""
    levels_collector = FilteredElementCollector(doc_param).OfClass(Level).ToElements()
    for level in levels_collector:
        try:
            if level.Name == level_name:
                return level
        except Exception as e:
            # print(f"# Warning: Error accessing level name for ID {level.Id}: {e}") # Escaped f-string
            pass
    print("# Error: Level named '{}' not found.".format(level_name))
    return None

def find_first_section_vft(doc_param):
    """Finds the first available Building Section ViewFamilyType."""
    vfts = FilteredElementCollector(doc_param).OfClass(ViewFamilyType).ToElements()
    for vft in vfts:
        # Check if it's a Section ViewType and specifically a Building Section
        # ViewFamily enum covers Section, Elevation, Detail etc.
        # We check the Name or other properties if needed, but ViewFamily should suffice
        # Note: Sometimes "Section" covers both Building and Wall sections.
        # A more robust check might look at the name containing "Building Section"
        # For this example, we take the first match for ViewType.Section.
        if vft.ViewFamily == ViewType.Section:
            # Optional: Add check for name like "Building Section" if multiple section types exist
            # if "Building Section" in vft.Name:
            #     return vft.Id
            return vft.Id # Return the first one found
    print("# Error: No Section View Family Type found in the document.")
    return ElementId.InvalidElementId

# --- Main Logic ---

# 1. Find the specified Level
target_level = find_level_by_name(doc, target_level_name)

# 2. Find a suitable Section ViewFamilyType
section_vft_id = find_first_section_vft(doc)

# 3. Proceed only if level and VFT are found
if target_level and section_vft_id != ElementId.InvalidElementId:
    try:
        level_elevation = target_level.ProjectElevation

        # Define the section box geometry
        # Origin point for the center of the section cut line at the level's elevation
        origin = XYZ(section_origin_x, section_origin_y, level_elevation)

        # Define the orientation (transform) for an E-W section looking East
        # BasisX defines the 'up' direction on the section marker (typically along model Z)
        # BasisY defines the view depth direction (perpendicular to the cut plane)
        # BasisZ defines the cut line direction (horizontal extent of the view)
        # Correction: API docs imply BBox XYZ relates to view coordinates AFTER transform.
        # Let's define a transform for a standard section cut.
        # View direction: Positive Y (North) -> Z = (0, 1, 0)
        # Right direction: Positive X (East) -> X = (1, 0, 0)
        # Up direction: Positive Z (Up) -> Y = (0, 0, 1)

        transform = Transform.Identity
        transform.Origin = origin
        # Set rotation for a section looking North (cutting East-West)
        transform.BasisX = XYZ.BasisX  # Right direction (East)
        transform.BasisY = XYZ.BasisZ  # Up direction
        transform.BasisZ = XYZ.BasisY  # View direction (North)


        # Define Min and Max corners of the BBox relative to the Transform's coordinate system
        # Min/Max X define the horizontal extents (width) along the cut line (transform.BasisX)
        # Min/Max Y define the vertical extents (height) (transform.BasisY)
        # Min/Max Z define the view depth (transform.BasisZ)

        min_x = -section_width / 2.0
        max_x = section_width / 2.0
        min_y = -height_below_level # Relative bottom height
        max_y = section_height - height_below_level # Relative top height
        min_z = -section_depth_far # Far clip plane distance (negative Z in view direction)
        max_z = section_depth_near # Near clip plane distance (often 0)

        section_box = BoundingBoxXYZ()
        section_box.Transform = transform
        section_box.Min = XYZ(min_x, min_y, min_z)
        section_box.Max = XYZ(max_x, max_y, max_z)

        # Create the new section view
        new_section_view = ViewSection.CreateSection(doc, section_vft_id, section_box)

        if new_section_view:
             # Attempt to rename the view for clarity
             try:
                  default_name = new_section_view.Name
                  new_name = "Section near {}".format(target_level_name)
                  # Basic check for existing name (optional)
                  existing_view_names = [v.Name for v in FilteredElementCollector(doc).OfClass(ViewSection).ToElements()]
                  counter = 1
                  final_view_name = new_name
                  while final_view_name in existing_view_names:
                      final_view_name = "{}_{}".format(new_name, counter)
                      counter += 1
                  new_section_view.Name = final_view_name
                  print("# Successfully created section view '{}'.".format(final_view_name))
             except Exception as rename_ex:
                  print("# Successfully created section view, but failed to rename. Default name: '{}'. Error: {}".format(default_name, rename_ex))

        else:
             print("# Failed to create section view for an unknown reason.")

    except Exception as create_ex:
        print("# Error creating section view for level '{}'. Error: {}".format(target_level_name, create_ex))

else:
    # Print messages about which prerequisite failed
    if not target_level:
        print("# Failed: Prerequisite Level '{}' not found.".format(target_level_name))
    if section_vft_id == ElementId.InvalidElementId:
        print("# Failed: Prerequisite Section View Family Type not found.")
    print("# View creation aborted due to missing prerequisites.")