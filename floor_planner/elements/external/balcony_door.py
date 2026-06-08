"""
Balcony Door element.

Draws in 2D identically to Door (frame + opening arc), but uses an external
OBJ model for 3D / glTF export.  The model contains a visible door frame,
a lower solid-wood wing panel, and an upper glass panel.

Author: Krzysztof Bartczak
"""

import math

import matplotlib.axes
from matplotlib.patches import Arc, Rectangle
from matplotlib.pylab import cos

from ...constants import RIGHT_ANGLE_IN_DEGREES
from ...utils import rotate_point
from ..external_models import ExternalModelElement
from ..symbols.info import DimensionArrow
from ...options import get_element_option
from ..vertical_levels import VertInfoDoor
from ..foundation.door import Door2D
from floor_planner.motion_3d import AnimationMetadata

class Door3D:
    def __init__(
            self,
            doorway_width: float,
            door_width: float,
            thickness: float,
            opening_outside: bool = False,
            to_the_right: bool = False,
            hinges_depth: float = 0.95
    ):
        self.doorway_width = doorway_width
        self.door_width = door_width
        self.opening_outside = opening_outside
        self.to_the_right = to_the_right
        self.thickness = thickness
        self.hinges_depth = hinges_depth


        self.secondary_normalization = {
                'scale':       [1, 1, 1],
                'rotation':    [0, 0, 0],
                'translation': [0, 0, 0],
            }
        self.secondary_anchor_offset = [0,0,0]      

    def getSecondaryNormalization(self):
        return self.secondary_normalization
    def getSecondaryAnchorOffset(self):
        return self.secondary_anchor_offset

    def calcNormalisationAndOffset(self):
    
        BASE_ROT = 22
        WING_WIDTH_ON_MODEL = 0.12  # The model's door wing is 0.12 m wide in the Z direction (wall thickness direction)
        MODEL_DOOR_WIDTH = 0.9      # The model's door wing is 0.9 m wide in the X direction (door-width direction)
        STREACH_TO_DOORFRAME = True     # Whether to stretch the model to fit the doorway width

        hinge_point = [0,0] # how to move the hinge point before applying rotation of wing
        x_shift = 0 # after rotation how much to move the door in X
        z_shift = 0 # after rotation how much to move the door in Z, inside a hole
        
        # K: Either stretch the model to fit the doorway or leave
        # a bit of room each side so the door is in the middle of the doorway.
        if STREACH_TO_DOORFRAME:
            space_for_door_wing = 0
            stretch_to_doorframe = self.doorway_width / MODEL_DOOR_WIDTH
        else:
            space_for_door_wing =  (self.doorway_width - self.door_width)/2
            stretch_to_doorframe = 1.0
        # Finally, the calculations for the secondary normalization (door swing) depend on
        # the opening direction and hinge side:
        if self.opening_outside:
            if self.to_the_right:
                #right outside
                open_deg = 180-BASE_ROT
                hinge_point = [0, WING_WIDTH_ON_MODEL]
                x_shift = self.doorway_width - space_for_door_wing
                z_shift = (self.thickness - WING_WIDTH_ON_MODEL)  * self.hinges_depth
                
            else:
                #left outside
                open_deg = BASE_ROT
                #hinge_point = [0, WING_WIDTH_ON_MODEL]
                hinge_point = [0, 0]
                x_shift = space_for_door_wing
                z_shift = (self.thickness - WING_WIDTH_ON_MODEL)  * self.hinges_depth
                
        else:    
            if self.to_the_right:
                #right inside
                open_deg = 180+BASE_ROT
                hinge_point = [0, 0]
                x_shift = self.doorway_width - space_for_door_wing
                z_shift = WING_WIDTH_ON_MODEL + (self.thickness - WING_WIDTH_ON_MODEL)  * self.hinges_depth
            else:
                #left inside
                open_deg = -BASE_ROT
                hinge_point = [0, WING_WIDTH_ON_MODEL ]
                x_shift = space_for_door_wing
                z_shift = WING_WIDTH_ON_MODEL + (self.thickness - WING_WIDTH_ON_MODEL)  * self.hinges_depth

        primary_translation = rotate_point([0,0], hinge_point[0], hinge_point[1], math.radians(open_deg))
        self.secondary_normalization = {
                'scale':       [stretch_to_doorframe, 1, 1],
                'rotation':    [0, open_deg, 0],
                'translation': [primary_translation[0],0,-primary_translation[1]],
            }
        self.secondary_anchor_offset = [-x_shift,0,-z_shift]


class BalconyDoor(VertInfoDoor, ExternalModelElement):
    """
    Balcony door element.

    In 2D floor plans this looks exactly like a regular Door (frame bars +
    opening arc).  In 3D / glTF export it uses an external OBJ model that
    shows a wooden frame, a solid lower panel, and a glazed upper panel.

    The external model has fixed dimensions (0.9 m × 2.1 m × 0.12 m).
    The 2D drawing honours the YAML-configured doorway_width, door_width
    and thickness parameters so the floor plan stays accurate.

    YAML parameters (same as Door):
        anchor_point     – (x, y) frame corner on the hinge side
        doorway_width    – total width including both frame sides (metres)
        door_width       – clear opening width (metres)
        thickness        – door / wall thickness (metres)
        orientation_angle – degrees counter-clockwise from X-axis
        to_the_right     – door swings to the right when False (default)
        hinges_point     – relative hinge position along thickness (0–1)
        opening_outside  – door opens outward when True
        color            – 2-D drawing colour (default 'black')
        label            – optional text label
    """

    _registry_key = 'balcony_door'
    _requires_external_model = True

    def __init__(
            self,
            anchor_point: tuple[float, float],
            doorway_width: float,
            door_width: float,
            thickness: float,
            door_orientation_in_doorway: float = 0.5,
            orientation_angle: float = 0,
            to_the_right: bool = False,
            color: str = 'black',
            hinges_point: float = 0.95,
            opening_outside: bool = False,
            label: str | None = None,
            **kwargs
    ):
        # ExternalModelElement.__init__ rejects 'width', 'length', 'height' in kwargs
        # but accepts all other keyword args (v_anchor, id, textures, etc.)
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            color=color,
            label=label,
            **kwargs
        )

        self.door2d = Door2D(anchor_point,doorway_width,door_width,thickness,
                orientation_angle,to_the_right,hinges_point,
                opening_outside,door_orientation_in_doorway)

        self.door3d = Door3D(
            doorway_width=doorway_width,
            door_width=door_width,
            thickness=thickness,
            opening_outside=opening_outside,
            to_the_right=to_the_right,
            hinges_depth= self.door2d.getHingesDepth()
        )


        # length and thickness  used by the parent Element / anchor helpers
        self.length = doorway_width
        self.thickness = thickness


        if True: # Krzysztof: my way of opening door on 3D:
            self.door3d.calcNormalisationAndOffset()  
            self.secondary_normalization = self.door3d.getSecondaryNormalization()
            self.secondary_anchor_offset = self.door3d.getSecondaryAnchorOffset()
            
            # Movable part desciptor as metadata under the 'animation' key in the child node 
            anim_meta = AnimationMetadata(AnimationMetadata.TriggerType.PROXIMITY)
            anim_meta.addTRS(translation=[0,0,0], rotation=[0, 90, 0], scale=[1,1,1])
                        
            anim_meta.addActivation(point=(doorway_width/2, 1.2 ,0.3 if self.door3d.opening_outside else -0.3),
                                    distance=(1.0, 0.5)
                                    )  
            # Todo, tune or remove that:
            anim_meta.addActivation( (1.0 ,2.0 ,3.0), (2.0, 0.3))

            self.animation = anim_meta.getAnimation()
            # Todo, tune or remove that:
            print("Animation metadata for balcony door:", self.animation)

        else:  # Krzysztof --- to do the animation refer here, by the AI ---

            # Door-specific 2D parameters (not touched by ExternalModelElement)
            self.doorway_width = doorway_width
            self.door_width = door_width
            self.thickness = thickness
            self.frame_width = (doorway_width - door_width) / 2
            self.to_the_right = to_the_right
            self.hinges_point = (1 - hinges_point) if opening_outside else hinges_point
            self.opening_outside = opening_outside

            # length is used by the parent Element / anchor helpers
            self.length = doorway_width

            # Secondary normalization: partially open the 3D door wing (≈ 15° from
            # the shut position) so the 3D view shows an ajar door that matches the
            # 2D floor-plan schematic.
            #
            # Model space (after primary normalization, anchor_offset = [0,0,0]):
            #   X ∈ [0, width]  → door-width direction
            #   Y ∈ [0, height] → vertical
            #   Z ∈ [0, depth]  → wall-thickness direction (Z=0 = room-side face)
            #
            # The hinge is on the X side closest to the YAML anchor_point.
            #   to_the_right=False  → hinge at X=0  (already at origin)
            #   to_the_right=True   → hinge at X=width (must shift, rotate, shift back)
            #
            # "Inside" opening → door swings toward Z+ (into the room shown above Z=0).
            #   Rotate around Y by +OPEN_DEG.
            # "Outside" opening → door swings toward Z- (outside).
            #   Rotate around Y by -OPEN_DEG.
            #
            # For to_the_right=True the hinge is at X=width, so we:
            #   1. secondary_anchor_offset = [width, 0, 0]   → moves hinge to origin
            #   2. Rotate (± OPEN_DEG) around Y              → door swings
            #   3. secondary_normalization translation = [width, 0, 0]  → moves back
            #
            # For to_the_right=False the hinge is already at origin, so anchor_offset
            # is [0,0,0] and translation = [0,0,0].

            OPEN_DEG = 22.0
            W = self._default_width()   # 0.9 m

            if to_the_right:
                # Hinge at X=W: shift to origin, rotate, shift back
                rot_y = OPEN_DEG if opening_outside else -OPEN_DEG
                self.secondary_normalization = {
                    'rotation':    [0, rot_y, 0],
                    'translation': [W, 0, 0],
                }
                self.secondary_anchor_offset = [W, 0, 0]
                # Animation pivot: hinge is at X=W in child-node space (after
                # secondary_anchor_offset moves it to origin, then the translation
                # puts it back at X=W in the parent's local space).
                _hinge_x = W
            else:
                # Hinge at X=0: already at origin
                rot_y = -OPEN_DEG if opening_outside else OPEN_DEG
                self.secondary_normalization = {
                    'rotation': [0, rot_y, 0],
                }
                self.secondary_anchor_offset = None
                _hinge_x = 0.0

            # Animation descriptor (Option B: metadata in glTF extras).
            # The 3D player reads child node extras.animation to drive door opening.
            # open_angle sign: positive = counter-clockwise around Y when viewed from above.
            # For opening_outside=False the door swings toward Z+ (into the room),
            # which is a positive Y-axis rotation; for opening_outside=True it is negative.
            _open_sign = -1.0 if opening_outside else 1.0
            self.animation = {
                'type':         'hinge_rotation',
                'axis':         [0, 1, 0],
                'pivot_local':  [_hinge_x, 0.0, 0.0],
                'closed_angle': 0.0,
                'open_angle':   _open_sign * 90.0,
                'duration':     0.5,
                'trigger':      'click',
            }
        

    # ------------------------------------------------------------------
    # ExternalModelElement hooks
    # ------------------------------------------------------------------

    def _default_width(self) -> float:
        return 0.9

    def _default_length(self) -> float:
        return 0.9

    def _default_height(self) -> float:
        return 2.1

    def get_to_the_right(self) -> bool:
        """Return whether the door opens to the right."""
        return self.door2d.to_the_right
   
    def get_doorway_width(self) -> float:
        """Return the doorway width."""
        return self.door2d.doorway_width
   
    def get_door_width(self) -> float:
        """Return the door width."""
        return self.door2d.door_width


    # ------------------------------------------------------------------
    # 2-D drawing – identical to Door.draw()
    # ------------------------------------------------------------------

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the balcony door exactly like a regular Door in 2D."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return
        z_order = self.get_zorder()
        self.door2d.draw2D(draw_color, z_order, ax)
        self.door2d.render_door_label_and_id(self, self.__class__.__name__, ax)
