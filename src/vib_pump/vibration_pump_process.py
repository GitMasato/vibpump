import argparse
import shutil
import sys
import pathlib as path
from ..image_process import binarize
from ..image_process import capture
from ..image_process import crop
from ..image_process import rotate
from ..file_system import directory_process as dir_proc
from input_info import InputInfo


class VibrationPumpProcess:
  def __init__(self):

    self.input = InputInfo()

  def CheckCommandLineArguments(self):

    parser = argparse.ArgumentParser(
      description="analysis software for vibration experiments",
      prog="vibration_pump.py",
    )

    parser.add_argument(
      "--files", nargs="*", type=str, required=True, metavar="file", help="movie files",
    )
    parser.add_argument(
      "--capture", action="store_true", help="flag to enable capture function",
    )
    parser.add_argument(
      "--rotate",
      action="store_true",
      help="flag to enable rotate function, requiring captured pictures",
    )
    parser.add_argument(
      "--crop",
      action="store_true",
      help="flag to enable crop function, requiring captured pictures",
    )
    parser.add_argument(
      "--binarize",
      action="store_true",
      help="flag to enable binarize function, requiring cropped pictures",
    )
    parser.add_argument(
      "--measure",
      action="store_true",
      help="flag to enable function of measuring climbing, requiring binarized pictures",
    )
    parser.add_argument(
      "--show",
      action="store_true",
      help="flag to enable function of showing data, requiring measured data",
    )
    parser.add_argument(
      "--clean", action="store_true", help="flag to clean analyzed data first",
    )

    args = parser.parse_args()
    print("setting inputs from command line arguments...")
    self.input.Set(
      args.files,
      args.capture,
      args.rotate,
      args.crop,
      args.binarize,
      args.measure,
      args.show,
      args.clean,
    )
    self.input.Show()

  def CheckExistenceOfMovieFiles(self):

    for movie in self.input.movies:
      if not path.Path(movie).is_file():
        sys.exit("[{0}] does not exist!".format(movie))

  def CaptureMovies(self):

    if not self.input.is_captured:
      return

    for movie in self.input.movies:
      capture.CaptureMovie(movie)

  def RotatePictures(self):

    if not self.input.is_rotated:
      return

    for movie in self.input.movies:
      movie_stem = path.Path(movie).stem
      capture_path = path.Path(path.Path.cwd() / "cv2" / movie_stem / "captured")
      try:
        rotate.RotatePicturesInDirectory(str(capture_path), "*_ms.jpg", -90.0)
      except FileNotFoundError as e:
        print(e)

  def CropPictures(self):

    if not self.input.is_cropped:
      return

    for movie in self.input.movies:
      crop.CropPicture(movie)

  #     pictures = list(mv_info.capture_path.glob("*_ms.jpg"))
  #     if not pictures:
  #       print("'{0}' does not have captured pictures!".format(mv_info.movie_path.name))
  #       sys.exit("crop function needs captured pictures")
  #     points = self.GetPositionsOfCroppingPicture(str(pictures[0]))

  #     for picture in pictures:

  #       file_name = picture.name
  #       img = cv2.imread(str(picture), 0)
  #       cropped = img[points[0][1] : points[1][1], points[0][0] : points[1][0]]
  #       cv2.imwrite(str(mv_info.crop_path) + "/" + file_name, cropped)

  #       if picture == pictures[-1]:
  #         self.SaveHistgramOfGrayPicture(mv_info, file_name, cropped)

  # def GetPositionsOfCroppingPicture(self, Picture):

  #   img = cv2.imread(Picture, 0)
  #   w, h = img.shape[1], img.shape[0]
  #   points = []
  #   cv2.namedWindow(Picture, cv2.WINDOW_NORMAL)
  #   cv2.setMouseCallback(Picture, self.MouseOnCrop, [Picture, img, w, h, points])
  #   self.AddLowerTextForCrop(
  #     img, ["s:save if selected", "c:clear", "click:select", "q/esc:abort "], h,
  #   )

  #   img_show = img.copy()
  #   self.AddUpperTextForCrop(img_show, ["crop:select two positions "])
  #   cv2.imshow(Picture, img_show)

  #   while True:

  #     k = cv2.waitKey(1) & 0xFF

  #     if k == ord("s"):
  #       if len(points) == 2:
  #         print("'s' is pressed. cropped positions are saved ({0})".format(points))
  #         cv2.destroyAllWindows()
  #         return points
  #       else:
  #         print("two positions for cropping are not selected yet")
  #         img_show = img.copy()
  #         self.AddUpperTextForCrop(img_show, ["crop:select two positions "])
  #         cv2.imshow(Picture, img_show)

  #     elif k == ord("c"):
  #       print("'c' is pressed. selected points are cleared")
  #       points.clear()
  #       img_show = img.copy()
  #       self.AddUpperTextForCrop(img_show, ["crop:select two positions "])
  #       cv2.imshow(Picture, img_show)

  #     elif k == ord("q"):
  #       cv2.destroyAllWindows()
  #       sys.exit("'q' is pressed. abort")

  #     elif k == 27:
  #       cv2.destroyAllWindows()
  #       sys.exit("'Esc' is pressed. abort")

  # def MouseOnCrop(self, event, x, y, flags, params):

  #   Picture, img, w, h, points = params

  #   if event == cv2.EVENT_LBUTTONUP:

  #     points.append([x, y])
  #     img_show = img.copy()

  #     if len(points) == 1:
  #       self.AddLineForCrop(img_show, points[0][0], points[0][1], w, h)
  #       self.AddUpperTextForCrop(
  #         img_show, ["selected[{0},{1}]".format(points[0][0], points[0][1])]
  #       )
  #     if len(points) == 2:

  #       if points[1][1] <= points[0][1] or points[1][0] <= points[0][0]:
  #         points.clear()
  #         self.AddUpperTextForCrop(
  #           img_show, ["2nd pos must be > 1st", "crop:select two positions "]
  #         )
  #       else:
  #         self.AddLineForCrop(img_show, points[0][0], points[0][1], w, h)
  #         self.AddLineForCrop(img_show, points[1][0], points[1][1], w, h)
  #         self.AddUpperTextForCrop(
  #           img_show,
  #           [
  #             "selected[{0},{1}]".format(points[0][0], points[0][1]),
  #             "selected[{0},{1}]".format(points[1][0], points[1][1]),
  #           ],
  #         )
  #     if len(points) == 3:
  #       points.clear()
  #       self.AddUpperTextForCrop(img_show, ["crop:select two positions "])

  #     cv2.imshow(Picture, img_show)

  # def AddUpperTextForCrop(self, Image, Texts):

  #   for id, Text in enumerate(Texts):
  #     pos_1 = (0, 0)
  #     pos_2 = (20 * len(Text), 30 * (id + 1))
  #     cv2.rectangle(Image, pos_1, pos_2, 255, -1)

  #   for id, Text in enumerate(Texts):
  #     pos = (5, 30 * (id + 1) - 2)
  #     cv2.putText(Image, Text, pos, cv2.FONT_HERSHEY_COMPLEX_SMALL, 1.6, 0, 2)

  # def AddLowerTextForCrop(self, Image, Texts, H):

  #   for id, Text in enumerate(Texts):
  #     pos_1 = (0, H - (30 * (id + 1)))
  #     pos_2 = (20 * len(Text), H)
  #     cv2.rectangle(Image, pos_1, pos_2, 255, -1)

  #   for id, Text in enumerate(Texts):
  #     pos = (5, H - (30 * id) - 4)
  #     cv2.putText(
  #       Image, Text, pos, cv2.FONT_HERSHEY_COMPLEX_SMALL, 1.6, 0, 2,
  #     )

  # def AddLineForCrop(self, Image, X, Y, W, H):

  #   cv2.line(Image, (X, 0), (X, H - 1), 255, 2)
  #   cv2.line(Image, (0, Y), (W - 1, Y), 255, 2)

  # def SaveHistgramOfGrayPicture(self, MV_Info, Capture_Name, Image):

  #   fig = plt.figure()
  #   subplot = fig.add_subplot(1, 2, 1)
  #   subplot.imshow(Image, cmap="gray")
  #   subplot.axis("off")

  #   subplot = fig.add_subplot(1, 2, 2)
  #   subplot.hist(Image.flatten(), bins=np.arange(256 + 1))
  #   fig.savefig(str(MV_Info.output_path) + "/histgram_" + Capture_Name)

  def BinarizePictures(self):

    if not self.input.is_binarized:
      return

    for movie in self.input.movies:
      binarize.BinarizePictures(movie)

  #     pictures = list(mv_info.crop_path.glob("*_ms.jpg"))
  #     if not pictures:
  #       print("'{0}' does not have cropped pictures!".format(mv_info.movie_path.name))
  #       sys.exit("binarize function needs cropped pictures")

  #     hist_picture = str(mv_info.output_path) + "/histgram_" + pictures[-1].name
  #     cropped_picture = str(pictures[-1])
  #     threshold = self.GetThresholdForBinarizingPicture(hist_picture, cropped_picture)

  #     for picture in pictures:

  #       file_name = picture.name
  #       img = cv2.imread(str(picture), 0)
  #       ret, bin_1 = cv2.threshold(img, threshold[0], 255, cv2.THRESH_TOZERO)
  #       ret, bin_2 = cv2.threshold(bin_1, threshold[1], 255, cv2.THRESH_TOZERO_INV)
  #       cv2.imwrite(str(mv_info.binarize_path) + "/" + file_name, bin_2)

  # def GetThresholdForBinarizingPicture(self, Hist_Picture, Cropped_Picture):

  #   hist_img = cv2.imread(Hist_Picture, 0)
  #   cropped_img = cv2.imread(Cropped_Picture, 0)
  #   cv2.namedWindow(Cropped_Picture, cv2.WINDOW_NORMAL)
  #   cv2.createTrackbar("low", Cropped_Picture, 0, 255, self.Nothing)
  #   cv2.createTrackbar("high", Cropped_Picture, 0, 255, self.Nothing)

  #   while True:

  #     low = cv2.getTrackbarPos("low", Cropped_Picture)
  #     high = cv2.getTrackbarPos("high", Cropped_Picture)
  #     cropped_img_show = cropped_img.copy()
  #     ret, bin_1 = cv2.threshold(cropped_img_show, low, 255, cv2.THRESH_TOZERO)
  #     ret, bin_2 = cv2.threshold(bin_1, high, 255, cv2.THRESH_TOZERO_INV)
  #     img_show = self.ConcatenatePictures([hist_img, bin_2])
  #     self.AddLowerTextForCrop(img_show, ["s:save", "q/esc:abort "], img_show.shape[0])

  #     if high < low:
  #       self.AddUpperTextForCrop(img_show, ["high must be > low"])
  #     else:
  #       self.AddUpperTextForCrop(img_show, ["adjust threshold"])
  #     cv2.imshow(Cropped_Picture, img_show)
  #     k = cv2.waitKey(1) & 0xFF

  #     if k == ord("s"):
  #       print("'s' is pressed. threshold is saved ({0}, {1})".format(low, high))
  #       cv2.destroyAllWindows()
  #       return [low, high]

  #     elif k == ord("q"):
  #       cv2.destroyAllWindows()
  #       sys.exit("'q' is pressed. abort")

  #     elif k == 27:
  #       cv2.destroyAllWindows()
  #       sys.exit("'Esc' is pressed. abort")

  # def Nothing(self, no):
  #   pass

  # def ConcatenatePictures(self, Pictures):

  #   min_y = min(Picture.shape[0] for Picture in Pictures)
  #   processed_pictures = [
  #     cv2.resize(
  #       Picture,
  #       (int(Picture.shape[1] * min_y / Picture.shape[0]), min_y),
  #       interpolation=cv2.INTER_CUBIC,
  #     )
  #     for Picture in Pictures
  #   ]
  #   return cv2.hconcat(processed_pictures)

  def MeasurePictures(self):

    if not self.input.is_measured:
      return

    for movie in self.input.movies:

      pictures = list(mv_info.binarize_path.glob("*_ms.jpg"))
      if not pictures:
        print("'{0}' does not have binarized pictures!".format(mv_info.movie_path.name))
        sys.exit("measure function needs binarized pictures")

      print("not implemented yet!")

  def ShowAnalyzedData(self):

    if not self.input.is_showed:
      return

  def CleanAnalyzedData(self):

    if not self.input.is_cleaned:
      return

    dir_path = path.Path(path.Path.cwd() / "analyzed")
    if dir_path.is_dir():
      shutil.rmtree(dir_path)
