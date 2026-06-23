"""
Group element: a container for other elements sharing a common anchor point.

Unlike Room, a Group does not require any walls and imposes no structural
constraints on its children. Groups can be nested recursively.

Author: Krzysztof Bartczak
"""


import copy
import matplotlib.axes

from ...variables import resolve_constants, resolve_element_params
from ..element import Element


class Group(Element):
    """
    A container element that groups other elements relative to a shared anchor point.

    A Group provides the same anchor-point translation as Room but does not
    require any walls and does not validate its contents in any way.
    Groups can be nested: a Group element may contain other Groups.
    """

    def __init__(
            self,
            child_elements: list | None = None,
            anchor_point: tuple[float, float] = (0, 0),
            color: str = 'black',
            label: str | None = None,
    ):
        """
        Initialize a group.

        :param child_elements:
            list of child element objects; may include nested Group instances
        :param anchor_point:
            coordinates (x, y) of the group's reference point; all child element
            positions defined in YAML are relative to this point
        :param color:
            default color (not used by Group itself but passed to Element for
            consistency with the rest of the hierarchy)
        :param label:
            optional label for the group (informational only)
        """
        super().__init__(anchor_point=anchor_point, label=label, color=color)
        self.child_elements = child_elements or []

    # ------------------------------------------------------------------
    # draw – Group itself draws nothing; children are already drawn as
    # they are added to the floor plan during create_from_params.
    # ------------------------------------------------------------------

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Group has no visual representation of its own."""
        pass

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def create_from_params(
            cls,
            params: dict,
            elements_registry: dict,
            floor_plan,
            all_elements: list,
            elements_by_id: dict,
            global_vars: dict | None = None,
    ) -> 'Group':
        """
        Create a Group from YAML parameters with nested elements.

        Supports recursive nesting: child elements whose type is ``group``
        are themselves created via this method.

        :param params:
            dictionary with an optional 'elements' list containing child element
            definitions, optional 'anchor_point', 'color', 'label', and 'vars'
        :param elements_registry:
            registry mapping element type names to classes
        :param floor_plan:
            floor plan to add child elements to (for rendering)
        :param all_elements:
            list to track all created elements
        :param elements_by_id:
            dictionary to track elements by ID
        :param global_vars:
            global variables dictionary (optional)
        :return:
            Group instance
        """
        if global_vars is None:
            global_vars = {}

        # Resolve group-scoped vars using global vars + previously resolved group vars
        group_vars_definitions = params.get('vars', params.get('constants', {}))
        group_vars: dict = {}
        for var_name, var_expression in group_vars_definitions.items():
            available_values = {**global_vars, **group_vars}
            group_vars[var_name] = resolve_constants(var_expression, available_values)

        # Resolve group-level parameters
        label = params.get('label')
        group_color = params.get('color', 'black')

        group_anchor_point = params.get('anchor_point', (0, 0))
        if 'anchor_point' in params:
            available_values = {**global_vars, **group_vars}
            group_anchor_point = resolve_constants(params['anchor_point'], available_values)

        element_defs = params.get('elements', [])

        child_elements: list = []

        for element_def in element_defs:
            element_def = copy.deepcopy(element_def)

            if not element_def.get('type'):
                raise ValueError(f"Element definition inside group missing 'type': {element_def}")

            element_type = element_def.pop('type')

            if element_type == 'group':
                # Recursive: nested group – pass merged vars down
                merged_vars = {**global_vars, **group_vars}

                # Translate the nested group's anchor_point by this group's anchor
                if 'anchor_point' in element_def:
                    rel_x, rel_y = resolve_constants(
                        element_def['anchor_point'], merged_vars
                    )
                    element_def['anchor_point'] = (
                        rel_x + group_anchor_point[0],
                        rel_y + group_anchor_point[1],
                    )

                nested_group = cls.create_from_params(
                    element_def,
                    elements_registry,
                    floor_plan,
                    all_elements,
                    elements_by_id,
                    global_vars=merged_vars,
                )
                floor_plan.add_element(nested_group)
                all_elements.append(nested_group)
                elements_by_id[nested_group.get_id()] = nested_group
                child_elements.append(nested_group)

            else:
                element_class = elements_registry.get(element_type)
                if not element_class:
                    raise ValueError(f"Unknown element type inside group: {element_type}")

                # Resolve vars in element parameters (group vars override global)
                element_def = resolve_element_params(element_def, global_vars, group_vars)

                # Translate anchor_point relative to this group's anchor
                if 'anchor_point' in element_def:
                    rel_x, rel_y = element_def['anchor_point']
                    element_def['anchor_point'] = (
                        rel_x + group_anchor_point[0],
                        rel_y + group_anchor_point[1],
                    )
                # Translate line endpoints
                if 'first_point' in element_def:
                    rel_x, rel_y = element_def['first_point']
                    element_def['first_point'] = (
                        rel_x + group_anchor_point[0],
                        rel_y + group_anchor_point[1],
                    )
                if 'second_point' in element_def:
                    rel_x, rel_y = element_def['second_point']
                    element_def['second_point'] = (
                        rel_x + group_anchor_point[0],
                        rel_y + group_anchor_point[1],
                    )

                element = element_class(**element_def)

                floor_plan.add_element(element)
                all_elements.append(element)
                elements_by_id[element.get_id()] = element
                child_elements.append(element)

        return cls(
            child_elements=child_elements,
            anchor_point=group_anchor_point,
            color=group_color,
            label=label,
        )
