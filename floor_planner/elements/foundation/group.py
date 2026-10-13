"""
Group element: a container for other elements sharing a common anchor point.

Unlike Room, a Group does not require any walls and imposes no structural
constraints on its children.  Groups can be nested recursively.

Room is a specialised Group that additionally validates its walls and
computes geometric properties.  Any element class that sets
``IS_CONTAINER = True`` is treated as a container by the shared
``_create_children`` helper and is instantiated via its own
``create_from_params`` classmethod rather than direct construction.

Author: Krzysztof Bartczak
"""


import copy
import matplotlib.axes

from ...variables import resolve_constants, resolve_element_params
from ..element import Element


class Group(Element):
    """
    A container element that groups other elements relative to a shared anchor point.

    A Group provides anchor-point translation for its children without imposing
    any structural constraints.  Groups can be nested: a child element whose
    class has ``IS_CONTAINER = True`` (e.g. another Group or a Room) is created
    via that class's ``create_from_params`` classmethod rather than direct
    instantiation.

    Groups support the ``from_template`` key in their YAML definition.  When
    present, the named template (registered via ``Group.register_templates``) is
    merged into the group params before instantiation:

    * template ``vars`` provide defaults; instance ``vars`` override them
    * template ``elements`` are the base list; instance ``elements`` are appended
    * instance ``anchor_point``, ``color``, ``label`` override template values

    Templates are registered once per config load (``__main__.py``) and are
    stored as a class-level dict, making them available to all nested
    ``create_from_params`` calls without threading an extra argument everywhere.
    """

    IS_CONTAINER = True

    # Class-level template registry: populated once per config load.
    _group_templates: dict = {}

    # ------------------------------------------------------------------
    # Template registry
    # ------------------------------------------------------------------

    @classmethod
    def register_templates(cls, templates: dict) -> None:
        """
        Register group templates from the ``group_templates`` YAML section.

        :param templates:
            dict mapping template names to their raw parameter dicts (not yet
            instantiated – just stored for later use by ``create_from_params``)
        """
        cls._group_templates = templates or {}

    @classmethod
    def _apply_template(cls, params: dict) -> dict:
        """
        If ``from_template`` is present in *params*, merge the named template
        into the params dict and return the result.  The original dict is not
        mutated.

        Merge rules
        -----------
        * ``vars``        – template vars are the base; instance vars override
        * ``elements``    – template elements first, instance elements appended
        * everything else – instance value wins (``anchor_point``, ``color``, …)

        :raises ValueError:
            if the referenced template name is not registered
        :raises ValueError:
            if a template definition itself contains ``from_template``
            (templates are not composable; that would add complexity for little gain)
        """
        template_name = params.get('from_template')
        if template_name is None:
            return params

        template = cls._group_templates.get(template_name)
        if template is None:
            raise ValueError(
                f"Group references unknown template {template_name!r}. "
                f"Known templates: {list(cls._group_templates)}"
            )
        if 'from_template' in template:
            raise ValueError(
                f"Template {template_name!r} itself contains 'from_template'. "
                "Template composition is not supported."
            )

        # Build merged params
        merged = dict(template)  # shallow copy of template as the base

        # vars: template defaults, instance overrides
        merged['vars'] = {**template.get('vars', {}), **params.get('vars', {})}

        # elements: template list first, instance additions appended
        merged['elements'] = (
            list(template.get('elements', [])) +
            list(params.get('elements', []))
        )

        # All other scalar keys from instance override template
        for key, value in params.items():
            if key not in ('vars', 'elements', 'from_template'):
                merged[key] = value

        return merged

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
            list of child element objects (may include nested Groups / Rooms)
        :param anchor_point:
            coordinates (x, y) of the group's reference point; child element
            positions defined in YAML are relative to this point
        :param color:
            default color passed down to walls that have no explicit color
        :param label:
            optional label (informational only)
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
    # Shared helpers used by Group.create_from_params and Room.create_from_params
    # ------------------------------------------------------------------

    @classmethod
    def _resolve_params(cls, params: dict, global_vars: dict) -> tuple:
        """
        Resolve scoped vars, anchor_point, color and label from container params.

        :param params:
            raw YAML parameter dict for this container
        :param global_vars:
            already-resolved global variables
        :return:
            (container_vars, anchor_point, color, label)
        """
        container_vars: dict = {}
        for var_name, var_expr in params.get('vars', params.get('constants', {})).items():
            container_vars[var_name] = resolve_constants(
                var_expr, {**global_vars, **container_vars}
            )

        color = params.get('color', 'black')
        label = params.get('label')
        anchor = params.get('anchor_point', (0, 0))
        if 'anchor_point' in params:
            anchor = resolve_constants(anchor, {**global_vars, **container_vars})

        return container_vars, anchor, color, label

    @classmethod
    def _create_children(
            cls,
            element_defs: list,
            elements_registry: dict,
            floor_plan,
            all_elements: list,
            elements_by_id: dict,
            global_vars: dict,
            container_vars: dict,
            anchor_point: tuple[float, float],
            color: str,
    ) -> list:
        """
        Instantiate child elements from a list of definition dicts.

        Elements whose class has ``IS_CONTAINER = True`` are created via
        ``create_from_params``; their ``anchor_point`` is pre-translated by
        this container's anchor before the recursive call.  All other elements
        are resolved with variable substitution and translated coordinate keys,
        then instantiated directly.

        :return:
            flat list of created child element instances
        """
        children: list = []
        merged_vars = {**global_vars, **container_vars}

        for element_def in element_defs:
            element_def = copy.deepcopy(element_def)

            if not element_def.get('type'):
                raise ValueError(f"Element definition missing 'type': {element_def}")

            element_type = element_def.pop('type')
            element_class = elements_registry.get(element_type)
            if element_class is None:
                raise ValueError(f"Unknown element type: {element_type!r}")

            if getattr(element_class, 'IS_CONTAINER', False):
                # Pre-translate the nested container's anchor before recursion
                if 'anchor_point' in element_def:
                    rel_x, rel_y = resolve_constants(
                        element_def['anchor_point'], merged_vars
                    )
                    element_def['anchor_point'] = (
                        rel_x + anchor_point[0],
                        rel_y + anchor_point[1],
                    )

                child = element_class.create_from_params(
                    element_def,
                    elements_registry,
                    floor_plan,
                    all_elements,
                    elements_by_id,
                    global_vars=merged_vars,
                )

            else:
                # Regular element: resolve vars then translate coordinate keys
                element_def = resolve_element_params(element_def, global_vars, container_vars)

                for coord_key in ('anchor_point', 'first_point', 'second_point'):
                    if coord_key in element_def:
                        rx, ry = element_def[coord_key]
                        try:
                            element_def[coord_key] = (
                                rx + anchor_point[0],
                                ry + anchor_point[1],
                            )
                        except:
                            raise ValueError(f"Issue with combining variables, the problem seems to be '{rx}' or '{ry}'")
                # Default wall color to the container color
                if element_type in ('wall', 'wallnd') and 'color' not in element_def:
                    element_def['color'] = color

                child = element_class(**element_def)

            floor_plan.add_element(child)
            all_elements.append(child)
            elements_by_id[child.get_id()] = child
            children.append(child)

        return children

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
        Create a Group from YAML parameters.

        :param params:
            dict with optional keys: ``elements``, ``anchor_point``, ``color``,
            ``label``, ``vars``
        :param elements_registry:
            registry mapping element type names to classes
        :param floor_plan:
            floor plan to add child elements to (for rendering)
        :param all_elements:
            list to track all created elements
        :param elements_by_id:
            dict to track elements by ID
        :param global_vars:
            global variables dictionary (optional)
        :return:
            Group instance
        """
        if global_vars is None:
            global_vars = {}

        params = cls._apply_template(params)

        container_vars, anchor, color, label = cls._resolve_params(params, global_vars)

        children = cls._create_children(
            params.get('elements', []),
            elements_registry,
            floor_plan,
            all_elements,
            elements_by_id,
            global_vars,
            container_vars,
            anchor,
            color,
        )

        return cls(child_elements=children, anchor_point=anchor, color=color, label=label)
