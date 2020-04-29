"""cli command for supporting vibpump projects.

image process:
basic required arguments is movie name and process name. if no movie and process is given, error will be raised.

output data (after image process) will be generated in 'cv2/target-noExtension/process-name/target' directory under current location (e.g. (test.mp4) ./cv2/test/binarized/test.png), except for 'measure' and 'graph' processes which will create '**_vib.csv' and '**_vib.png' data in ./cv2 directory.

simulation:
this supports LIGGGHTS simulations.

see usage '-h option'

"""
import argparse
import imghdr
import pathlib
import sys
from typing import List
from imgproc import api
from vibpump import image


def call_image(
  args: argparse.Namespace, parser: argparse.ArgumentParser, opt_args: List[str]
):
  """call function when image command is given
  """
  items = [value for key, value in args.__dict__.items() if key != "call"]
  if not [item for item in items if (item is not None) and (item is not False)]:
    sys.exit(parser.parse_args(["image", "--help"]))

  if {"--binarize", "--capture", "--crop", "--measure", "--rotate"} & set(opt_args):

    movie_list: List[str] = []
    if args.movie:
      for movie in args.movie:
        movie_path = pathlib.Path(movie)
        if movie_path.is_file():
          if imghdr.what(movie) is None:
            movie_list.append(movie)

    if not movie_list:
      sys.exit("no movie exists!")

    if args.type:
      if args.type == "binarized":
        input_data = image.get_input_list(movie_list, "binarized")
      elif args.type == "captured":
        input_data = image.get_input_list(movie_list, "captured")
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
        input_data = api.binarize(input_data)
      elif opt == "--capture":
        input_data = api.capture(input_data)
      elif opt == "--crop":
        input_data = api.crop(input_data)
      elif opt == "--measure":
        input_data = image.measure(input_data, movie_list)
      elif opt == "--rotate":
        input_data = api.rotate(input_data)

  if set(["--graph"]) & set(opt_args):
    image.graph()


def call_liggghts(args: argparse.Namespace, parser: argparse.ArgumentParser):
  """call function when liggghts command is given
  """
  items = [value for key, value in args.__dict__.items() if key != "call"]
  if not [item for item in items if (item is not None) and (item is not False)]:
    sys.exit(parser.parse_args(["liggghts", "--help"]))


def call_liggghts_setup(args: argparse.Namespace, parser: argparse.ArgumentParser):
  """call function when liggghts setup command is given
  """
  items = [value for key, value in args.__dict__.items() if key != "call"]
  if not [item for item in items if (item is not None) and (item is not False)]:
    sys.exit(parser.parse_args(["liggghts", "setup", "--help"]))


def call_liggghts_analyze(args: argparse.Namespace, parser: argparse.ArgumentParser):
  """call function when liggghts analyze command is given
  """
  items = [value for key, value in args.__dict__.items() if key != "call"]
  if not [item for item in items if (item is not None) and (item is not False)]:
    sys.exit(parser.parse_args(["liggghts", "analyze", "--help"]))


def cli_execution():
  """read, parse, and execute cli arguments
  """
  parser = argparse.ArgumentParser(
    prog="vibpump.py",
    formatter_class=argparse.RawTextHelpFormatter,
    description="python package providing functions for vibpump project.",
  )
  subparsers = parser.add_subparsers()

  parser_image = subparsers.add_parser(
    "image",
    formatter_class=argparse.RawTextHelpFormatter,
    help="execute image-prcessing of experimental movies",
    description="sub-command 'image': execute image prcessing of experimental movies"
    + "\n\noutput is generated in 'cv2' directory under current location."
    + "\nif multiple processes are selected, input data is processed continuously"
    + "\nin order of argument. (output in one process is given to the next process.)"
    + "\n'--graph' process is exceptional and executed at the end."
    + "\n\n'--movie' option means path of movie."
    + "\nif '--type' is not selected, movie file itself is given as input."
    + "\nif '--type' option is selected, pre-processed data for the movie in 'cv2'"
    + "\ndirecotry under current location is given as input."
    + "\nif pre-processed data does not exist, image process is not executed."
    + "\n\nwhether '--type' is selected or not, movie file itself must exist."
    + "\nif it does not exist, image process is not executed except for '--graph'."
    + "\n'--measure' option creates '**_vib.csv' that cannot be given to other process."
    + "\n'--graph' visualize .csv file. if any '_**vib.csv' exists in 'cv2' directory,"
    + "\n'--graph' process can run and does not require movie or pre-processed data."
    + "\n\n(see sub-option 'image -h')"
    + "\n ",
  )
  parser_image.set_defaults(call=call_image)
  parser_image.add_argument(
    "--movie", nargs="*", type=str, metavar="path", help="movie file path" + "\n ",
  )
  parser_image.add_argument(
    "--type",
    choices=["binarized", "captured", "cropped", "rotated"],
    help="target type"
    + "\nif this is not selected, movie file itself is given as input."
    + "\nif selected, the pre-processed directory of movie in 'cv2' direcotry"
    + "\nunder current location is given as input."
    + "\n ",
  )
  parser_image.add_argument(
    "--binarize", action="store_true", help="to enable binarize process" + "\n ",
  )
  parser_image.add_argument(
    "--capture",
    action="store_true",
    help="to enable capture process, requiring 'movie' type input (no '--type' option)"
    + "\nthis process should be executed first."
    + "\n ",
  )
  parser_image.add_argument(
    "--crop", action="store_true", help="to enable crop process" + "\n ",
  )
  parser_image.add_argument(
    "--graph",
    action="store_true",
    help="to visualize measured data, requiring csv file in 'cv2' directory"
    + "\nthis creates .png image and python script for visualization."
    + "\n ",
  )
  parser_image.add_argument(
    "--measure",
    action="store_true",
    help="to measure climbing height, requiring 'binarized' type input"
    + "\nthis creates .csv file in 'cv2' directory, and output file name is decided"
    + "\nusing first movie file name. this should be executed just after 'binarize'."
    + "\n ",
  )
  parser_image.add_argument(
    "--rotate", action="store_true", help="to enable rotate process" + "\n ",
  )

  parser_liggghts = subparsers.add_parser(
    "liggghts",
    formatter_class=argparse.RawTextHelpFormatter,
    help="support liggghts simulation",
    description="sub-command 'liggghts': support liggghts simulation"
    + "\n\nnot implemented",
  )
  parser_liggghts.set_defaults(call=call_liggghts)
  subparsers_liggghts = parser_liggghts.add_subparsers()

  subparser_liggghts = subparsers_liggghts.add_parser(
    "setup",
    formatter_class=argparse.RawTextHelpFormatter,
    help="support liggghts simulation",
    description="sub-command 'liggghts.setup': support liggghts simulation"
    + "\n\nnot implemented",
  )
  subparser_liggghts.add_argument(
    "--target", nargs="*", type=str, metavar="path", help="target path" + "\n ",
  )
  parser_liggghts.set_defaults(call=call_liggghts_setup)

  subparser_liggghts = subparsers_liggghts.add_parser(
    "analyze",
    formatter_class=argparse.RawTextHelpFormatter,
    help="support liggghts simulation",
    description="sub-command 'liggghts.analyze': support liggghts simulation"
    + "\n\nnot implemented",
  )
  subparser_liggghts.add_argument(
    "--target", nargs="*", type=str, metavar="path", help="target path" + "\n ",
  )
  parser_liggghts.set_defaults(call=call_liggghts_analyze)

  if len(sys.argv) <= 1:
    sys.exit(parser.format_help())

  args = parser.parse_args()
  if args.call.__name__ == "call_image":
    args.call(args, parser, sys.argv[2:])
  else:
    args.call(args, parser)


def main() -> None:
  """cli command main function
  """
  cli_execution()


if __name__ == "__main__":
  main()
