"""cli command for supporting vibpump projects.

image commad:
basic required arguments is movie name and process name.
if no movie and process is given, error will be raised.

output data (after image process) will be generated in
'cv2/target-noExtension/process-name/target' directory under current location
(e.g. (test.mp4) ./cv2/test/binarized/test.png).

liggghts command:
this supports LIGGGHTS simulations. (subcommands: 'preprocess', 'postprocess')
basic required arguments is ini file name (**.ini).

see usage '-h option'

"""
import argparse
import imghdr
import pathlib
import sys
from typing import List
from imgproc import api
from vibpump import image
from vibpump import liggghts


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


def call_liggghts_pre(args: argparse.Namespace, parser: argparse.ArgumentParser):
  """call function when liggghts preprocess command is given
  """
  items = [value for key, value in args.__dict__.items() if key != "call"]
  if not [item for item in items if (item is not None) and (item is not False)]:
    sys.exit(parser.parse_args(["liggghts", "preprocess", "--help"]))

  ini_list: List[str] = []
  if args.ini:
    for ini in args.ini:
      if ".ini" in ini:
        ini_list.append(ini)

  if not ini_list:
    sys.exit("no .ini file exists!")

  liggghts.setup_simulation(ini_list, args.cluster)

  if args.execute:
    liggghts.execute_simulation(ini_list, args.cluster)
    liggghts.animate(ini_list, args.cluster)


def call_liggghts_post(args: argparse.Namespace, parser: argparse.ArgumentParser):
  """call function when liggghts postprocess command is given
  """
  items = [value for key, value in args.__dict__.items() if key != "call"]
  if not [item for item in items if (item is not None) and (item is not False)]:
    sys.exit(parser.parse_args(["liggghts", "postprocess", "--help"]))

  ini_list: List[str] = []
  if args.ini:
    for ini in args.ini:
      if ".ini" in ini:
        ini_list.append(ini)

  if not ini_list:
    sys.exit("no .ini file exists!")

  if args.animate:
    liggghts.animate(ini_list, args.cluster, args.fps)

  if args.measureHeight:
    liggghts.measure_height(ini_list, args.cluster)

  if args.graphHeight:
    liggghts.graph_height(ini_list, args.cluster)


def cli_execution():
  """read, parse, and execute cli arguments
  """
  parser = argparse.ArgumentParser(
    prog="vibpump.py",
    formatter_class=argparse.RawTextHelpFormatter,
    description="python package providing functions for vibpump project.",
  )
  subparsers = parser.add_subparsers()

  # parser for image function
  parser_image = subparsers.add_parser(
    "image",
    formatter_class=argparse.RawTextHelpFormatter,
    help="command for executing image-prcessing of experimental movies",
    description="command 'image': execute image prcessing of experimental movies\n\n"
    + "output is generated in 'cv2' directory under current location.\n"
    + "if multiple processes are selected, input data is processed continuously\n"
    + "in order of argument. (output in one process is given to the next process.)\n"
    + "'--graph' process is exceptional and executed at the end.\n\n"
    + "'--movie' option means path of movie.\n"
    + "if '--type' is not selected, movie file itself is given as input.\n"
    + "if '--type' option is selected, pre-processed data for the movie in 'cv2'\n"
    + "direcotry under current location is given as input.\n"
    + "if pre-processed data does not exist, image process is not executed.\n\n"
    + "whether '--type' is selected or not, movie file itself must exist.\n"
    + "if it does not exist, image process is not executed except for '--graph'.\n"
    + "'--measure' option creates '**_vib.csv' that cannot be given to other process.\n"
    + "'--graph' visualize .csv file. if any '_**vib.csv' exists in 'cv2' directory,\n"
    + "'--graph' process can run and does not require movie or pre-processed data.\n\n"
    + "(see sub-option 'vibpump image -h')\n",
  )
  parser_image.set_defaults(call=call_image)
  parser_image.add_argument(
    "--movie", nargs="*", type=str, metavar="path", help="movie file path" + "\n ",
  )
  parser_image.add_argument(
    "--type",
    choices=["binarized", "captured", "cropped", "rotated"],
    help="target type\n"
    + "if this is not selected, movie file itself is given as input.\n"
    + "if selected, the pre-processed directory of movie in 'cv2' direcotry\n"
    + "under current location is given as input.\n",
  )
  parser_image.add_argument(
    "--binarize", action="store_true", help="to enable binarize process" + "\n ",
  )
  parser_image.add_argument(
    "--capture",
    action="store_true",
    help="to enable capture process, requiring 'movie' input (no '--type' option)\n"
    + "this process should be executed first.\n",
  )
  parser_image.add_argument(
    "--crop", action="store_true", help="to enable crop process" + "\n ",
  )
  parser_image.add_argument(
    "--graph",
    action="store_true",
    help="to visualize measured data, requiring csv file in 'cv2' directory\n"
    + "this creates .png image and python script for visualization.\n",
  )
  parser_image.add_argument(
    "--measure",
    action="store_true",
    help="to measure climbing height, requiring 'binarized' type input\n"
    + "this creates .csv file in 'cv2' directory, and output file name is decided\n"
    + "using first movie file name. this should be executed just after 'binarize'.\n",
  )
  parser_image.add_argument(
    "--rotate", action="store_true", help="to enable rotate process" + "\n ",
  )

  # parser for liggghts function
  parser_liggghts = subparsers.add_parser(
    "liggghts",
    formatter_class=argparse.RawTextHelpFormatter,
    help="command for supporting liggghts simulation",
    description="command 'liggghts': support liggghts simulation\n\n"
    + "(see sub-option 'vibpump liggghts -h')\n",
  )
  parser_liggghts.set_defaults(call=call_liggghts)
  subparsers_liggghts = parser_liggghts.add_subparsers()

  # parser for liggghts setup function
  subparser_pre = subparsers_liggghts.add_parser(
    "pre",
    formatter_class=argparse.RawTextHelpFormatter,
    help="command for preprocess of simulation",
    description="command 'liggghts pre': preprocess of simulation\n\n"
    + "basic required arguments is ini file (**.ini. '--ini').\n\n"
    + "(see sub-option 'vibpump liggghts pre -h')\n",
  )
  subparser_pre.add_argument(
    "--ini",
    nargs="*",
    type=str,
    metavar="path",
    help="path to ini file (**.ini)" + "\n ",
  )
  subparser_pre.add_argument(
    "--cluster",
    action="store_true",
    help="to generate files for running on cluster" + "\n ",
  )
  subparser_pre.add_argument(
    "--execute",
    action="store_true",
    help="to start simulations using generated files" + "\n ",
  )
  subparser_pre.set_defaults(call=call_liggghts_pre)

  # parser for liggghts analyze function
  subparser_post = subparsers_liggghts.add_parser(
    "post",
    formatter_class=argparse.RawTextHelpFormatter,
    help="command for postprocess of simulation",
    description="command 'liggghts post': postprocess of simulation\n\n"
    + "basic required arguments is ini file (**.ini. '--ini').\n\n"
    + "(see sub-option 'vibpump liggghts post -h')\n",
  )
  subparser_post.add_argument(
    "--ini",
    nargs="*",
    type=str,
    metavar="path",
    help="path to ini file (**.ini)" + "\n ",
  )
  subparser_post.add_argument(
    "--cluster",
    action="store_true",
    help="to generate files for running on cluster" + "\n ",
  )
  subparser_post.add_argument(
    "--animate",
    action="store_true",
    help="to create movie file from simulation results" + "\n ",
  )

  subparser_post.add_argument(
    "--fps",
    type=int,
    metavar="fps",
    default=None,
    help="fps when to create movie file from simulation results" + "\n ",
  )
  subparser_post.add_argument(
    "--measureHeight",
    action="store_true",
    help="to measure climbing height from simulation results" + "\n ",
  )
  subparser_post.add_argument(
    "--graphHeight",
    action="store_true",
    help="to graph climbing height results" + "\n ",
  )
  subparser_post.set_defaults(call=call_liggghts_post)

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
