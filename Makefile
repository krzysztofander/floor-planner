PYTHON = .venv/bin/python3
PYSRC = $(wildcard floor_planner/*.py)
PYSRC += $(wildcard floor_planner/elements/*.py)
PYSRC += $(wildcard floor_planner/elements/landscaping/*.py)

.PHONY: all clean room_templates elements furniture simple landscaping extras tests

all: room_templates elements furniture simple landscaping

# ==========================================

# ROOM TEMPLATES
# --------------
## Root directory for room templates
ROOM_TEMPLATES_ROOT = examples/templates/rooms
## List of room template folders
ROOM_TEMPLATES = room_north room_south room_east room_west play_with_doors

## Generate paths for each room template
ROOM_TEMPLATE_MAINS = $(foreach ex,$(ROOM_TEMPLATES),$(ROOM_TEMPLATES_ROOT)/$(ex)/project_main.yml)
ROOM_TEMPLATE_OUTPUTS = $(foreach ex,$(ROOM_TEMPLATES),$(ROOM_TEMPLATES_ROOT)/$(ex)/output/some_floor.png)

# Main target to build all room templates
room_templates: $(ROOM_TEMPLATE_OUTPUTS)

# Pattern rule: build output for each example by processing its project_main.yml
$(ROOM_TEMPLATES_ROOT)/%/output/some_floor.png: $(ROOM_TEMPLATES_ROOT)/%/project_main.yml $(ROOM_TEMPLATES_ROOT)/%/*.yml $(PYSRC)
	@echo "Processing $<"
	$(PYTHON) -m floor_planner -c $<

# INDIVIDUAL ELEMENTS
# -------------------
ELEMENTS_PNG = examples/elements/Individual_elements.png
elements: $(ELEMENTS_PNG)

$(ELEMENTS_PNG): examples/elements/all_elements.yml $(PYSRC)
	@echo "Processing $<"
	$(PYTHON) -m floor_planner -c $<


FURNITURE_PNG = examples/elements/Beds_Rotation_Test.png
furniture: $(FURNITURE_PNG)

$(FURNITURE_PNG): examples/elements/furniture_demo.yml $(PYSRC)
	@echo "Processing $<"
	$(PYTHON) -m floor_planner -c $<

#OTHER
#-----
SIMPLE_PNG = examples/simple_no_rooms/Plain_floor_plan.png
simple: $(SIMPLE_PNG)

$(SIMPLE_PNG): examples/simple_no_rooms/simple_floor_plan.yml $(PYSRC)
	@echo "Processing $<"
	$(PYTHON) -m floor_planner -c $<

# LANDSCAPING
# -----------
LANDSCAPING_VEGETATION_PNG = examples/landscaping/Case_1_No_Species_No_Bloom.png
LANDSCAPING_HARDSCAPE_PNG = examples/landscaping/Hardscape_Elements_Demo.png
LANDSCAPING_WATER_PNG = examples/landscaping/Water_Features_Demo.png
LANDSCAPING_STRUCTURES_PNG = examples/landscaping/Garden_Structures_Demo.png
LANDSCAPING_PNG = $(LANDSCAPING_VEGETATION_PNG) $(LANDSCAPING_HARDSCAPE_PNG) $(LANDSCAPING_WATER_PNG) $(LANDSCAPING_STRUCTURES_PNG)
landscaping: $(LANDSCAPING_PNG)

$(LANDSCAPING_VEGETATION_PNG): examples/landscaping/vegetation_demo.yml $(PYSRC)
	@echo "Processing $<"
	$(PYTHON) -m floor_planner -c $<

$(LANDSCAPING_HARDSCAPE_PNG): examples/landscaping/hardscape_demo.yml $(PYSRC)
	@echo "Processing $<"
	$(PYTHON) -m floor_planner -c $<

$(LANDSCAPING_WATER_PNG): examples/landscaping/water_features_demo.yml $(PYSRC)
	@echo "Processing $<"
	$(PYTHON) -m floor_planner -c $<

$(LANDSCAPING_STRUCTURES_PNG): examples/landscaping/structures_demo.yml $(PYSRC)
	@echo "Processing $<"
	$(PYTHON) -m floor_planner -c $<

# EXTRAS
# ------
EXTRAS_PNG = examples/landscaping/Comprehensive_Landscaping_Site_Plan.png 
EXTRAS_PNG += examples/3d_visualization/Simple_Room_-_3D_Export_Demo.png
EXTRAS_PNG += examples/3d_visualization/Furnished_Room_-_3D_Visualization.png
extras: $(EXTRAS_PNG)

$(word 1,$(EXTRAS_PNG)): examples/landscaping/site_plan_complete.yml $(PYSRC)
	@echo "Processing $<"
	$(PYTHON) -m floor_planner -c $<

$(word 2,$(EXTRAS_PNG)): examples/3d_visualization/simple_room.yml $(PYSRC)
	@echo "Processing $<"
	$(PYTHON) -m floor_planner -c $<

$(word 3,$(EXTRAS_PNG)): examples/3d_visualization/furnished_room.yml $(PYSRC)
	@echo "Processing $<"
	$(PYTHON) -m floor_planner -c $<


# TESTS
# -----
TESTS_PNG = tests/test_invisible_openings/output/Invisible_Openings_Test.png
TESTS_PNG += tests/doors_and_windows/Doors_and_windows.png
TESTS_PNG += tests/test_shadows_with_opened_walls/output/Invisible_Openings_Test.png
TESTS_PNG += tests/test_wall_openings/output/openings.png
TESTS_PNG += tests/play_with_doors/output/some_floor.png
TESTS_PNG += tests/all_elements/output/All_Elements.png
TESTS_PNG += tests/play_with_double_doors/output/some_floor.png
TESTS_PNG += tests/vege/output/vege.png


tests: $(TESTS_PNG)

$(word 1,$(TESTS_PNG)): tests/test_invisible_openings/project_main.yml tests/test_invisible_openings/*.yml $(PYSRC)
	@echo "Processing $<"
	$(PYTHON) -m floor_planner -c $<

$(word 2,$(TESTS_PNG)): tests/doors_and_windows/doors_and_windows.yml $(PYSRC)
	@echo "Processing $<"
	$(PYTHON) -m floor_planner -c $<

$(word 3,$(TESTS_PNG)): tests/test_shadows_with_opened_walls/project_main.yml tests/test_shadows_with_opened_walls/*.yml $(PYSRC)
	@echo "Processing $<"
	$(PYTHON) -m floor_planner -c $<

$(word 4,$(TESTS_PNG)): tests/test_wall_openings/project_main.yml tests/test_wall_openings/*.yml $(PYSRC)
	@echo "Processing $<"
	$(PYTHON) -m floor_planner -c $<

$(word 5,$(TESTS_PNG)): tests/play_with_doors/project_main.yml tests/play_with_doors/*.yml $(PYSRC)
	@echo "Processing $<"
	$(PYTHON) -m floor_planner -c $<

$(word 6,$(TESTS_PNG)): tests/all_elements/project_main.yml tests/all_elements/*.yml $(PYSRC)
	@echo "Processing $<"
	$(PYTHON) -m floor_planner -c $<

$(word 7,$(TESTS_PNG)): tests/play_with_double_doors/project_main.yml tests/play_with_double_doors/*.yml $(PYSRC)
	@echo "Processing $<"
	$(PYTHON) -m floor_planner -c $<

$(word 8,$(TESTS_PNG)): tests/vege/project_main.yml tests/vege/*.yml $(PYSRC)
	@echo "Processing $<"
	$(PYTHON) -m floor_planner -c $<


# Clean generated outputs
clean:
	rm -f $(ROOM_TEMPLATE_OUTPUTS)
	rm -f $(ELEMENTS_PNG)
	rm -f $(SIMPLE_PNG)
	rm -f $(LANDSCAPING_PNG)
	rm -f $(EXTRAS_PNG)
	rm -f $(TESTS_PNG)

