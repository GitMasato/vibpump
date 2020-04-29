"""image module containing image process functions
"""
import csv
import cv2
import inspect
import numpy
import math
import pathlib
import re
from matplotlib import pyplot
from typing import List, Tuple, Optional


def add_texts(image: numpy.array, texts: List[str], position: Tuple[int, int]):
  """add texts into cv2 object

  Args:
      image (numpy.array): cv2 image object
      texts (List[str]): texts
      position (Tuple[int, int]): position to add texts
  """
  for id, text in enumerate(texts):
    pos = (position[0], position[1] + 30 * (id + 1))
    cv2.putText(image, text, pos, cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 10)
    cv2.putText(image, text, pos, cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 0, 0), 2)


def add_texts_upper_left(image: numpy.array, texts: List[str]):
  """add texts into upper left corner of cv2 object

  Args:
      image (numpy.array): cv2 image object
      texts (List[str]): texts
  """
  pos = (5, 0)
  add_texts(image, texts, pos)


def add_texts_upper_right(image: numpy.array, texts: List[str]):
  """add texts into upper right corner of cv2 object

  Args:
      image (numpy.array): cv2 image object
      texts (List[str]): texts
  """
  W = image.shape[1]
  str_len = max([len(text) for text in texts])
  pos = (W - (18 * str_len), 0)
  add_texts(image, texts, pos)


def add_texts_lower_left(image: numpy.array, texts: List[str]):
  """add texts into lower left corner of cv2 object

  Args:
      image (numpy.array): cv2 image object
      texts (List[str]): texts
  """
  H = image.shape[0]
  pos = (5, H - 15 - (30 * len(texts)))
  add_texts(image, texts, pos)


def add_texts_lower_right(image: numpy.array, texts: List[str]):
  """add texts into lower right corner of cv2 object

  Args:
      image (numpy.array): cv2 image object
      texts (List[str]): texts
  """
  W, H = image.shape[1], image.shape[0]
  str_len = max([len(text) for text in texts])
  pos = (W - (18 * str_len), H - 15 - (30 * len(texts)))
  add_texts(image, texts, pos)


def mouse_on_select_positions(event, x, y, flags, params):
  """call back function on mouse click
  """
  points = params
  if event == cv2.EVENT_LBUTTONUP:
    points.append((x, y))


def no(no):
  """meaningless function just for trackbar callback"""
  pass


def get_movie_info(cap: cv2.VideoCapture) -> Tuple[int, int, int, float]:
  """get movie information

  Args:
      cap (cv2.VideoCapture): cv2 video object

  Returns:
      Tuple[int, int, int, float]: W, H, total frame, fps of movie
  """
  W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
  H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
  fps = cap.get(cv2.CAP_PROP_FPS)
  temp_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
  temp_frames = temp_frames - int(fps) if int(fps) <= temp_frames else temp_frames
  cap.set(cv2.CAP_PROP_POS_FRAMES, temp_frames)

  # CAP_PROP_FRAME_COUNT is usually not correct.
  # so take temporal frame number first, then find the correct number
  while True:
    ret, frame = cap.read()
    if not ret:
      break
  frames = int(cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1
  cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
  return (W, H, frames, fps)


def get_input_list(target_list: List[str], input_type: str) -> List[str]:
  """get output path list

  Args:
      target_list (List[str]): list of pictures or movies or directories where pictures are stored
      type (str): output type

  Returns:
      List[str]: list of input
  """
  path_list: List[str] = []
  cv2_path = pathlib.Path(pathlib.Path.cwd() / "cv2")

  for target in target_list:
    target_path = pathlib.Path(target)
    input_path = pathlib.Path(cv2_path / target_path.stem / input_type)

    if input_path.is_dir():
      path_list.append(str(input_path))
    else:
      print("'{0}' does not exist!".format(str(input_path)))

  return path_list


def measure(target_list: List[str], movie_list: List[str]):
  """measure climbing height (this require binarized data and movie)

  Args:
      target_list (List[str]): list of binarized data of movie
      movie_list (List[str]): list of movie
  """
  target_tuple_list: List[Tuple[str, str]] = []
  cv2_path = pathlib.Path(pathlib.Path.cwd() / "cv2")

  for movie in movie_list:
    movie_path = pathlib.Path(movie)
    input_path = pathlib.Path(cv2_path / movie_path.stem / "binarized")
    for target in target_list:
      if target == str(input_path):
        target_tuple_list.append((target, movie))

  if not set(target_tuple_list):
    print("no movie to be read exists!")
    return None

  regex = re.compile("\d{8,10}")
  output_name = str(cv2_path) + "/" + pathlib.Path(movie_list[0]).stem + "_vib.csv"
  with open(output_name, "w") as f:

    for target_tuple in set(target_tuple_list):

      cap = cv2.VideoCapture(target_tuple[1])
      W, H, frames, fps = get_movie_info(cap)
      mm_per_pixel = select_referene_length(target_tuple[0], frames, cap)
      if mm_per_pixel is None:
        continue

      binarized_path = pathlib.Path(target_tuple[0])
      p_list = [str(p) for p in list(binarized_path.iterdir())]
      if not p_list:
        print("no file exists in '{0}'!".format(target_tuple[0]))
        continue

      places = select_reference_place(target_tuple[0], p_list)
      if not places:
        continue

      bottom, tube_pos, threshold = places
      time_list: List[float] = []
      height_list: List[float] = []

      for p in p_list:
        match = regex.findall(p)
        if not match:
          continue

        time = float(match[-1]) * 0.001
        img = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
        cut = img[:bottom, tube_pos[0] : tube_pos[1]]
        height = bottom

        for idx, y in enumerate(cut):
          white_size = numpy.count_nonzero(y)
          white_area = white_size / len(y) * 100.0
          if threshold <= white_area:
            height = idx
            break
        time_list.append(time)
        height_list.append((bottom - height) * mm_per_pixel)

      if height_list:
        w = csv.writer(f)
        w.writerow(["time_s_{0}".format(target_tuple[1])] + [str(t) for t in time_list])
        w.writerow(
          ["height_mm_{0}".format(target_tuple[1])] + [str(t) for t in height_list]
        )


def select_referene_length(
  movie: str, frames: int, cap: cv2.VideoCapture,
) -> Optional[float]:
  """select(get) reference length using GUI window

  Args:
      movie (str): movie file name
      frames (int): total frame of movie
      cap (cv2.VideoCapture): cv2 video object

  Returns:
      Optional[float]: mm per pixel
  """
  cv2.namedWindow(movie, cv2.WINDOW_NORMAL)
  cv2.resizeWindow(movie, 500, 700)
  help_exists = False

  division = 100
  tick = division if division < frames else frames
  tick_s = (int)(frames / division) + 1
  cv2.createTrackbar("frame\n", movie, 0, tick - 1, no)
  cv2.createTrackbar("frame s\n", movie, 0, tick_s, no)
  cv2.createTrackbar("mm/line\n", movie, 0, 100, no)

  points: List[Tuple[int, int]] = []
  warning_message: List[str] = []
  cv2.namedWindow(movie, cv2.WINDOW_NORMAL)
  cv2.setMouseCallback(movie, mouse_on_select_positions, points)
  line_color = (255, 255, 255)

  print("--- measure ---")
  print("select line mm/pixel in GUI window!")
  print("(s: save if selected, h:on/off help, c: clear, click: select, q/esc: abort)")

  while True:

    frame = cv2.getTrackbarPos("frame\n", movie) * tick_s
    frame_s = cv2.getTrackbarPos("frame s\n", movie)
    frame_now = frame + frame_s if frame + frame_s < frames else frames
    mm_per_line = cv2.getTrackbarPos("mm/line\n", movie)
    if mm_per_line == 0:
      mm_per_line = 1

    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_now)
    ret, img = cap.read()

    if len(points) == 1:
      cv2.drawMarker(img, points[0], line_color, markerSize=10)
    elif len(points) == 2:
      cv2.drawMarker(img, points[0], line_color, markerSize=10)
      cv2.drawMarker(img, points[1], line_color, markerSize=10)
      cv2.line(img, points[0], points[1], line_color, 2)
    elif len(points) == 3:
      points.clear()
      warning_message = ["3rd is not accepted"]

    if help_exists:
      add_texts_lower_right(
        img,
        [
          "s:save if selected",
          "h:on/off help",
          "c:clear",
          "click:select",
          "q/esc:abort",
        ],
      )
      add_texts_upper_left(
        img,
        [
          "[measure]",
          "select line and mm/pixel",
          "frame: {0}".format(frame_now),
          "mm/line: {0}".format(mm_per_line),
        ],
      )
      add_texts_lower_left(img, warning_message)

    cv2.imshow(movie, img)
    k = cv2.waitKey(1) & 0xFF

    if k == ord("s"):
      if len(points) == 2:
        cv2.destroyAllWindows()
        reference_length = math.sqrt(
          (points[1][0] - points[0][0]) ** 2 + (points[1][1] - points[0][1]) ** 2
        )
        print(
          "'s' is pressed. mm/pixel is saved ({0:.2f})".format(
            mm_per_line / reference_length
          )
        )
        return mm_per_line / reference_length
      else:
        print("line is not selected yet")
        warning_message = ["not selected yet"]
        continue

    elif k == ord("c"):
      print("'c' is pressed. selected points are cleared")
      points.clear()
      warning_message = ["cleared"]
      continue

    elif k == ord("h"):
      if help_exists:
        help_exists = False
      else:
        help_exists = True
      continue

    elif k == ord("q"):
      cv2.destroyAllWindows()
      print("'q' is pressed. abort")
      return None

    elif k == 27:
      cv2.destroyAllWindows()
      print("'Esq' is pressed. abort")
      return None


def select_reference_place(
  directory: str, picture_list: List[str]
) -> Optional[Tuple[int, Tuple[int, int], int]]:
  """select(get) three reference lines and threshold using GUI window

  Args:
      directory (str): directory name
      picture_list (List[str]): picture list

  Returns:
      Optional[int, Tuple[int, int], int]: bottom line for measurement, tube position lines, threshold % for determining if particles are filled or not
  """
  cv2.namedWindow(directory, cv2.WINDOW_NORMAL)
  cv2.resizeWindow(directory, 500, 700)
  help_exists = False

  frames = len(picture_list) - 1
  division = 50
  tick = division if division < frames else frames
  tick_s = (int)(frames / division) + 1
  cv2.createTrackbar("frame\n", directory, 0, tick - 1, no)
  cv2.createTrackbar("frame s\n", directory, 0, tick_s, no)
  cv2.createTrackbar("threshold\n%", directory, 0, 100, no)

  points: List[Tuple[int, int]] = []
  warning_message: List[str] = []
  cv2.setMouseCallback(directory, mouse_on_select_positions, points)
  white = 255

  print("--- measure ---")
  print("select three reference lines and threshold in GUI window!")
  print("(s: save if selected, h:on/off help, c: clear, click: select, q/esc: abort)")

  while True:

    frame = cv2.getTrackbarPos("frame\n", directory) * tick_s
    frame_s = cv2.getTrackbarPos("frame s\n", directory)
    frame_now = frame + frame_s if frame + frame_s < frames else frames
    threshold = cv2.getTrackbarPos("threshold\n%", directory)
    if threshold == 0:
      threshold = 1

    img = cv2.imread(picture_list[frame_now], cv2.IMREAD_GRAYSCALE)
    W, H = img.shape[1], img.shape[0]

    if len(points) == 1:
      cv2.line(img, (0, points[0][1]), (W - 1, points[0][1]), white, 2)
    elif len(points) == 2:
      cv2.line(img, (0, points[0][1]), (W - 1, points[0][1]), white, 2)
      cv2.line(img, (points[1][0], 0), (points[1][0], H - 1), white, 2)
    elif len(points) == 3:
      if points[2][0] <= points[1][0]:
        points.clear()
        warning_message = ["x_2 must be > x_1"]
      else:
        cut = img[: points[0][1], points[1][0] : points[2][0]]
        for idx, y in enumerate(cut):
          white_size = numpy.count_nonzero(y)
          white_area = white_size / len(y) * 100.0
          if threshold <= white_area:
            cv2.line(img, (points[1][0], idx), (points[2][0], idx), white, 2)
            break

        cv2.line(img, (0, points[0][1]), (W - 1, points[0][1]), white, 2)
        cv2.line(img, (points[1][0], 0), (points[1][0], H - 1), white, 2)
        cv2.line(img, (points[2][0], 0), (points[2][0], H - 1), white, 2)

    elif len(points) == 4:
      points.clear()
      warning_message = ["4th is not accepted"]

    if help_exists:
      add_texts_lower_right(
        img,
        [
          "s:save if selected",
          "h:on/off help",
          "c:clear",
          "click:select",
          "q/esc:abort",
        ],
      )
      add_texts_upper_left(
        img,
        [
          "[measure]",
          "select area",
          "frame: {0}".format(frame_now),
          "threshold: {0}%".format(threshold),
        ],
      )
      add_texts_lower_left(img, warning_message)

    cv2.imshow(directory, img)
    k = cv2.waitKey(1) & 0xFF

    if k == ord("s"):
      if len(points) == 3:
        cv2.destroyAllWindows()
        print(
          "'s' is pressed. area and threshold are saved ({0},{1},{2})".format(
            points[0][1], (points[1][0], points[2][0]), threshold
          )
        )
        return (points[0][1], (points[1][0], points[2][0]), threshold)
      else:
        print("area and threshold are not selected yet")
        warning_message = ["not selected yet"]
        continue

    elif k == ord("c"):
      print("'c' is pressed. selected points are cleared")
      points.clear()
      warning_message = ["cleared"]
      continue

    elif k == ord("h"):
      if help_exists:
        help_exists = False
      else:
        help_exists = True
      continue

    elif k == ord("q"):
      cv2.destroyAllWindows()
      print("'q' is pressed. abort")
      return None

    elif k == 27:
      cv2.destroyAllWindows()
      print("'Esq' is pressed. abort")
      return None


def graph():
  """visualize measured height
  """
  cv2_path = pathlib.Path(pathlib.Path.cwd() / "cv2")
  files = [str(p) for p in cv2_path.iterdir() if p.is_file() and ("_vib.csv" in str(p))]

  for file in files:
    with open(file) as f:
      reader = csv.reader(f)
      data = {}
      for row in reader:
        data[row[0]] = [float(r) for r in row[1:]]

    if not data:
      print("no data exists in {0}!".format(file))
      continue

    data_sets = set([d.lstrip("time_s_").lstrip("height_mm_") for d in data.keys()])
    if not data_sets:
      print("no data for vibpump experiment exists!")
      continue

    pyplot.rcParams["xtick.direction"] = "in"
    pyplot.rcParams["ytick.direction"] = "in"
    pyplot.figure(figsize=(4.5, 3), dpi=300)
    blue_cmap = pyplot.get_cmap("Blues")
    time_max = 0.0

    for idx, val in enumerate(list(data_sets)):
      if ("time_s_" + val not in data) or ("height_mm_" + val not in data):
        continue
      tm = max(data["time_s_" + val])
      time_max = tm if time_max < tm else tm
      pyplot.plot(
        data["time_s_" + val],
        data["height_mm_" + val],
        c=blue_cmap(1.0 - (0.1 * idx)),
        ls="solid",
        lw=0.7,
        label=pathlib.Path(val).stem,
      )

    pyplot.xlabel("time  $\it{s}$")
    pyplot.ylabel("climbing height $\it{mm}$")
    pyplot.xlim(xmin=0, xmax=time_max)
    # pyplot.xticks([0, 15, 30, 45], [0, 15, 30, 45], rotation=0)
    # pyplot.ylim(ymin=0,ymax=1000)
    # pyplot.yticks([0,10,20,30,40,50], [0,10,20,30,40,50], rotation=0)
    pyplot.grid(which="minor")
    pyplot.legend(bbox_to_anchor=(1, 1.01), loc="lower right", borderaxespad=0)
    pyplot.savefig(file.replace(".csv", ".png"), bbox_inches="tight")
    # pyplot.show()
    pyplot.close()
    output_helper(file)


def output_helper(file: str):

  text = "import csv\nimport pathlib\nfrom matplotlib import pyplot\n\n\n"
  text += inspect.getsource(graph)
  helper_path = pathlib.Path(file.replace(".csv", ".py"))
  helper_path.write_text(text.rstrip("output_helper(file)\n") + "\n")
