"""cli command for supporting vibpump project.

basic required arguments are movie name and process name.
if no movie and process is given, error will be raised.

output data (after image process) will be generated in
'cv2/target-noExtension/process-name/target' directory under current location
(e.g. (test.mp4) ./cv2/test/binarized/test.png).

see usage using '-h' option

"""
import argparse
import imghdr
import pathlib
import sys
from typing import List
from imgproc import api
from vibpump import image


def call_image_process(args: argparse.Namespace, parser: argparse.ArgumentParser,
                       opt_args: List[str]):
  """call function when image command is given"""
  items = [value for key, value in args.__dict__.items() if key != "call"]
  if not [item for item in items if (item is not None) and (item is not False)]:
    sys.exit(parser.parse_args(["image", "--help"]))

  if {"--binarize", "--capture", "--clip", "--crop", "--measure", "--rotate"
     } & set(opt_args):

    movie_list: List[str] = []
    if args.movie:
      for movie in args.movie:
        movie_path = pathlib.Path(movie)
        if movie_path.is_file():
          if imghdr.what(movie) is None:
            movie_list.append(movie)

    if not movie_list:
      sys.exit("no movie file exists!")

    if args.type:
      if args.type == "binarized":
        input_data = image.get_input_list(movie_list, "binarized")
      elif args.type == "captured":
        input_data = image.get_input_list(movie_list, "captured")
      elif args.type == "clipped":
        input_data = image.get_input_list(movie_list, "clipped")
      elif args.type == "cropped":
        input_data = image.get_input_list(movie_list, "cropped")
      elif args.type == "rotated":
        input_data = image.get_input_list(movie_list, "rotated")
    else:
      input_data = movie_list.copy()

    if not input_data:
      sys.exit("no input exists!")

    for opt in opt_args:
      if opt == "--binarize":
        input_data = api.binarize(target_list=input_data)
      elif opt == "--capture":
        input_data = api.capture(target_list=input_data)
      elif opt == "--clip":
        input_data = api.clip(target_list=input_data)
      elif opt == "--crop":
        input_data = api.crop(target_list=input_data)
      elif opt == "--measure":
        input_data = image.measure(input_data, movie_list)
      elif opt == "--rotate":
        input_data = api.rotate(target_list=input_data)

  if set(["--graph"]) & set(opt_args):
    image.graph(args.movie)


def cli_execution():
  """read, parse, and execute cli arguments"""
  parser = argparse.ArgumentParser(
      prog="vibpump.py",
      formatter_class=argparse.RawTextHelpFormatter,
      description="python package providing functions for vibpump project.\n\n" +
      "output is generated in 'cv2' directory under current location.\n" +
      "if multiple processes are selected, input data is processed continuously\n" +
      "in order of argument. (output in one process is given to the next process.)\n" +
      "'--graph' process is exceptional and executed at the end.\n\n" +
      "'--movie' option means path of movie.\n" +
      "if '--type' is not selected, movie file itself is given as input.\n" +
      "if '--type' option is selected, pre-processed data for the movie in 'cv2'\n" +
      "direcotry under current location is given as input.\n" +
      "if pre-processed data does not exist, image process is not executed.\n\n" +
      "whether '--type' is selected or not, movie file itself must exist.\n" +
      "if it does not exist, image process is not executed except for '--graph'.\n" +
      "'--measure' creates '**_height.csv' that can be given only to '--graph',.\n" +
      "visualizing .csv file. if multiple '**_height.csv' are given,\n" +
      "'--graph' creates one figure containing multiple data in 'cv2' directory.\n\n" +
      "(see sub-option 'vibpump image -h')\n",
  )

  parser.set_defaults(call=call_image_process)
  parser.add_argument(
      "--movie",
      nargs="*",
      type=str,
      metavar="path",
      help="movie file path" + "\n ",
  )
  parser.add_argument(
      "--type",
      choices=["binarized", "captured", "clipped", "cropped", "rotated"],
      help="target type\n" +
      "if this is not selected, movie file itself is given as input.\n" +
      "if selected, the pre-processed directory of movie in 'cv2' direcotry\n" +
      "under current location is given as input.\n",
  )
  parser.add_argument(
      "--binarize",
      action="store_true",
      help="to enable binarize process" + "\n ",
  )
  parser.add_argument(
      "--capture",
      action="store_true",
      help="to enable capture process, requiring 'movie' input (no '--type' option)\n" +
      "this process should be executed first.\n",
  )
  parser.add_argument(
      "--clip",
      action="store_true",
      help="to enable clip process" + "\n",
  )
  parser.add_argument(
      "--crop",
      action="store_true",
      help="to enable crop process" + "\n ",
  )
  parser.add_argument(
      "--graph",
      action="store_true",
      help="to visualize measured data, requiring csv file in 'cv2' directory\n" +
      "this creates .png image and python script for visualization.\n",
  )
  parser.add_argument(
      "--measure",
      action="store_true",
      help="to measure climbing height, requiring 'binarized' type input\n" +
      "this creates .csv file in 'cv2' directory, and output file name is decided\n" +
      "using first movie file name. this should be executed just after 'binarize'.\n",
  )
  parser.add_argument(
      "--rotate",
      action="store_true",
      help="to enable rotate process" + "\n ",
  )

  if len(sys.argv) <= 1:
    sys.exit(parser.format_help())

  args = parser.parse_args()
  args.call(args, parser, sys.argv[2:])


def main() -> None:
  """cli command main function"""
  cli_execution()


if __name__ == "__main__":
  main()
