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

from ...layers import pop_layer
from ...options import get_element_option
from ...variables import resolve_constants, resolve_element_params
from ..element import Element
from ..symbols.info import DimensionArrow


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

    ``embedded_dimensions: false`` skips every ``dimension_arrow`` defined
    within the container, including those inside nested groups and rooms.

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
            id: str | None = None,
            embedded_dimensions: bool = True,
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
        :param id:
            optional explicit ID; if None, generated from class name and label
        :param embedded_dimensions:
            if False, dimension arrows defined within this container (and any
            nested container) are skipped (never created), so they are not rendered
        """
        super().__init__(anchor_point=anchor_point, label=label, color=color, id=id)
        self.child_elements = child_elements or []
        self.embedded_dimensions = embedded_dimensions

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
    def _resolve_params(
            cls,
            params: dict,
            global_vars: dict,
            parent_offset: tuple[float, float] = (0, 0),
    ) -> tuple:
        """
        Resolve scoped vars, anchor_point, color and label from container params.

        The container's ``anchor_point`` is resolved in the container's own
        scope (``global_vars`` plus this container's vars, which cover outer
        names) and then translated by ``parent_offset``.  This is the same for
        top-level containers (offset ``(0, 0)``) and nested ones (offset = the
        parent's absolute anchor).  A container without ``anchor_point`` assumes
        ``(0, 0)`` relative to its parent, i.e. it sits at ``parent_offset``.

        :param params:
            raw YAML parameter dict for this container
        :param global_vars:
            variables visible from outside the container (global vars plus the
            vars of all enclosing containers)
        :param parent_offset:
            absolute anchor of the enclosing container; ``(0, 0)`` at top level
        :return:
            (container_vars, anchor_point, color, label); ``anchor_point`` is
            an absolute ``(x, y)`` tuple
        """
        container_vars: dict = {}
        for var_name, var_expr in params.get('vars', params.get('constants', {})).items():
            container_vars[var_name] = resolve_constants(
                var_expr, {**global_vars, **container_vars}
            )

        color = params.get('color', 'black')
        label = params.get('label')
        rel_x, rel_y = resolve_constants(
            params.get('anchor_point', (0, 0)), {**global_vars, **container_vars}
        )
        try:
            anchor = (rel_x + parent_offset[0], rel_y + parent_offset[1])
        except TypeError:
            raise ValueError(
                f"{cls.__name__} {label or ''}: cannot resolve anchor_point "
                f"{params.get('anchor_point')!r}, the problem seems to be '{rel_x}' or '{rel_y}'"
            )

        return container_vars, anchor, color, label

    @classmethod
    def _resolve_embedded_dimensions(cls, params: dict) -> bool:
        """
        Return the container's ``embedded_dimensions`` flag.

        Lookup order: the container's own ``embedded_dimensions`` param, then
        the floor plan option of the same name for this class (``Group`` or
        ``Room``), then True.
        """
        if 'embedded_dimensions' in params:
            return bool(params['embedded_dimensions'])
        return bool(get_element_option(cls.__name__, 'embedded_dimensions', True))

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
            embedded_dimensions: bool = True,
    ) -> list:
        """
        Instantiate child elements from a list of definition dicts.

        Elements whose class has ``IS_CONTAINER = True`` are created via
        ``create_from_params`` with ``parent_offset`` set to this container's
        anchor; the nested container resolves its own ``anchor_point`` in its
        own scope and adds that offset.  All other elements are resolved with
        variable substitution and translated coordinate keys, then
        instantiated directly.

        When ``embedded_dimensions`` is False, ``DimensionArrow`` definitions
        are skipped and nested containers are forced to
        ``embedded_dimensions: false`` too, so the setting covers everything
        defined within this container.

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

            if not embedded_dimensions and issubclass(element_class, DimensionArrow):
                continue

            if getattr(element_class, 'IS_CONTAINER', False):
                if not embedded_dimensions:
                    element_def['embedded_dimensions'] = False

                # The nested container resolves its own anchor_point (in its
                # own scope) and translates it by this container's anchor.
                child = element_class.create_from_params(
                    element_def,
                    elements_registry,
                    floor_plan,
                    all_elements,
                    elements_by_id,
                    global_vars=merged_vars,
                    parent_offset=anchor_point,
                )

            else:
                # Regular element: resolve vars then translate coordinate keys
                layer = pop_layer(element_def, element_type)
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
                child.set_layer(layer)

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
            parent_offset: tuple[float, float] = (0, 0),
    ) -> 'Group':
        """
        Create a Group from YAML parameters.

        :param params:
            dict with optional keys: ``elements``, ``anchor_point``, ``color``,
            ``label``, ``vars``, ``embedded_dimensions``
        :param elements_registry:
            registry mapping element type names to classes
        :param floor_plan:
            floor plan to add child elements to (for rendering)
        :param all_elements:
            list to track all created elements
        :param elements_by_id:
            dict to track elements by ID
        :param global_vars:
            variables visible from outside the group (optional)
        :param parent_offset:
            absolute anchor of the enclosing container; ``(0, 0)`` at top level
        :return:
            Group instance
        """
        if global_vars is None:
            global_vars = {}

        params = cls._apply_template(params)

        container_vars, anchor, color, label = cls._resolve_params(params, global_vars, parent_offset)
        embedded_dimensions = cls._resolve_embedded_dimensions(params)

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
            embedded_dimensions,
        )

        return cls(child_elements=children, anchor_point=anchor, color=color, label=label, id=params.get('id'),
                   embedded_dimensions=embedded_dimensions)
