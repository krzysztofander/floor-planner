"""
Provide class to encode the movable elements like doors opening
"""


from enum import IntEnum

from floor_planner.utils import WarnMsg


class AnimationMetadata:
    class TriggerType(IntEnum):
        PROXIMITY = 1
        LOOK_AT = 2
        CLICK = 3
        # Add more trigger types as needed

    def __init__(
            self,type # proximity, click, look_at, etc.
    ):
        self.type = type
        self.data = list()
        self.translation = (-1,-2,-3) # some charateristic init
        self.rotation = (-4,-5,-6)
        self.scale = (-7,-8,-9)

    def addTRS(self, translation: tuple[float, float, float], rotation: tuple[float, float, float], scale: tuple[float, float, float]):
        """Add transformation parameters for the animation."""
        self.translation = translation
        self.rotation = rotation
        self.scale = scale

    def addActivation(self, point: tuple[float, float, float], distance: tuple[float, float]):
        """Add an activation point for proximity or look_at triggers as well as the activation distances"""
        if (self.type == self.TriggerType.PROXIMITY) or (self.type == self.TriggerType.LOOK_AT):
            for p in point:
                self.data.append(p)
            for d in distance:
                self.data.append(d)

    def getAnimation(self):
        """Build the animation metadata dictionary based on the trigger type and parameters."""
        if self.type == self.TriggerType.PROXIMITY:
            d = {
                'type': 'proximity',
                'translation': self.translation,
                'rotation': self.rotation,
                'scale': self.scale,
                'data': self.data,
           }
            return d
        WarnMsg("Unsupported trigger type for animation metadata:", self.type)
        return None
