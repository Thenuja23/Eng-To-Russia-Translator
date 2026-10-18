from .transform import ImageTransform
from .lines import LineSegmenter


class PreprocessingPipeline:
    def __init__(self):
        self.transform = ImageTransform()
        self.lines = LineSegmenter()

    def process(self, img):
        img = self.transform.perspective_correction(img)
        img = self.transform.deskew(img)
        img = self.transform.remove_shadows(img)
        img = self.transform.deslant(img)
        img = self.transform.normalize_height(img, pad_width=True)
        return img
