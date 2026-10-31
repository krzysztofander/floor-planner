"""
Process-wide state of floor_planner and how to reset it.

Running several projects in one process (e.g. in the test suite) must give the
same result as running each of them alone; ``run_project`` therefore starts
with ``reset_global_state()``.
"""

import matplotlib.pyplot as plt

from floor_planner import options
from floor_planner.elements.element import Element
from floor_planner.elements.foundation.group import Group


def reset_global_state() -> None:
    """
    Reset all process-wide state that a project run changes.

    - ``Element._element_counter`` (adds a per-element offset to ``v_anchor``)
    - generated element ID counters
    - per-element-type drawing options
    - registered group templates
    - open matplotlib figures

    Pure caches (``rotate_point``, per-class default ``textures``) need no reset.
    """
    Element._element_counter = 0
    options.reset_id_counters()
    options.set_element_options({})
    Group.register_templates({})
    plt.close('all')
