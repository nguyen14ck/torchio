from typing import Union, Tuple
import torch
import numpy as np
from ....torchio import DATA, AFFINE
from ....utils import is_image_dict
from ... import Transform


TypeBounds = Union[
    int,
    Tuple[int, int, int],
    Tuple[int, int, int, int, int, int],
]


class BoundsTransform(Transform):
    def __init__(
            self,
            bounds_parameters: TypeBounds,
            ):
        super().__init__()
        self.bounds_parameters = self.parse_bounds(bounds_parameters)

    @property
    def bounds_function(self):
        raise NotImplementedError

    def parse_bounds(
            self,
            bounds_parameters: TypeBounds,
            ) -> Tuple[int, ...]:
        try:
            bounds_parameters = tuple(bounds_parameters)
        except TypeError:
            bounds_parameters = (bounds_parameters,)
        bounds_parameters_length = len(bounds_parameters)
        if bounds_parameters_length == 6:
            return bounds_parameters
        elif bounds_parameters_length == 1:
            return 6 * bounds_parameters
        elif bounds_parameters_length == 3:
            return tuple(np.repeat(bounds_parameters, 2).tolist())
        message = (
            'Bounds parameter must be an integer or a tuple of'
            f' 3 or 6 integers, not {bounds_parameters}'
        )
        raise ValueError(message)

    def apply_transform(self, sample: dict) -> dict:
        low = self.bounds_parameters[::2]
        high = self.bounds_parameters[1::2]
        for image_dict in sample.values():
            if not is_image_dict(image_dict):
                continue
            image = self.nib_to_sitk(image_dict[DATA][0], image_dict[AFFINE])
            result = self.bounds_function(image, low, high)
            data, affine = self.sitk_to_nib(result)
            tensor = torch.from_numpy(data).unsqueeze(0)
            image_dict[DATA] = tensor
            image_dict[AFFINE] = affine
        return sample
