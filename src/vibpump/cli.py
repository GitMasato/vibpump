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


def call_liggghts_setup(args: argparse.Namespace, parser: argparse.ArgumentParser):
  """call function when liggghts setup command is given
  """
  items = [value for key, value in args.__dict__.items() if key != "call"]
  if not [item for item in items if (item is not None) and (item is not False)]:
    sys.exit(parser.parse_args(["liggghts", "setup", "--help"]))

  ini_list: List[str] = []
  if args.ini:
    for ini in args.ini:
      if ".ini" in ini:
        ini_list.append(ini)

  if not ini_list:
    sys.exit("no .ini file exists!")

  liggghts.setup(ini_list, args.cluster, args.animate, args.execute)


def call_liggghts_execute(args: argparse.Namespace, parser: argparse.ArgumentParser):
  """call function when liggghts execute command is given
  """
  items = [value for key, value in args.__dict__.items() if key != "call"]
  if not [item for item in items if (item is not None) and (item is not False)]:
    sys.exit(parser.parse_args(["liggghts", "execute", "--help"]))

  ini_list: List[str] = []
  if args.ini:
    for ini in args.ini:
      if ".ini" in ini:
        ini_list.append(ini)

  if not ini_list:
    sys.exit("no .ini file exists!")

  liggghts.execute(ini_list, args.cluster)


def call_liggghts_copy(args: argparse.Namespace, parser: argparse.ArgumentParser):
  """call function when liggghts copy command is given
  """
  items = [value for key, value in args.__dict__.items() if key != "call"]
  if not [item for item in items if (item is not None) and (item is not False)]:
    sys.exit(parser.parse_args(["liggghts", "copy", "--help"]))

  ini_list: List[str] = []
  if args.ini:
    for ini in args.ini:
      if ".ini" in ini:
        ini_list.append(ini)

  if not ini_list:
    sys.exit("no .ini file exists!")

  liggghts.copy_results(ini_list, args.logSim, args.logPost)


def call_liggghts_log(args: argparse.Namespace, parser: argparse.ArgumentParser):
  """call function when liggghts log command is given
  """
  items = [value for key, value in args.__dict__.items() if key != "call"]
  if not [item for item in items if (item is not None) and (item is not False)]:
    sys.exit(parser.parse_args(["liggghts", "log", "--help"]))

  ini_list: List[str] = []
  if args.ini:
    for ini in args.ini:
      if ".ini" in ini:
        ini_list.append(ini)

  if not ini_list:
    sys.exit("no .ini file exists!")

  liggghts.display_log(ini_list, args.head, args.process, args.line)


def call_liggghts_process(args: argparse.Namespace, parser: argparse.ArgumentParser):
  """call function when liggghts process command is given
  """
  items = [value for key, value in args.__dict__.items() if key != "call"]
  if not [item for item in items if (item is not None) and (item is not False)]:
    sys.exit(parser.parse_args(["liggghts", "process", "--help"]))

  ini_list: List[str] = []
  if args.ini:
    for ini in args.ini:
      if ".ini" in ini:
        ini_list.append(ini)

  if not ini_list:
    sys.exit("no .ini file exists!")

  # if args.animate:
  #   liggghts.animate(ini_list, args.cluster, args.fps)

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
  subparser_setup = subparsers_liggghts.add_parser(
    "setup",
    formatter_class=argparse.RawTextHelpFormatter,
    help="command for setup of simulation",
    description="command 'liggghts setup': to generate files for simulation\n\n"
    + "basic required arguments is ini file (**.ini. '--ini').\n\n"
    + "(see sub-option 'vibpump liggghts setup -h')\n",
  )
  subparser_setup.add_argument(
    "--ini",
    nargs="*",
    type=str,
    metavar="path",
    help="path to ini file (**.ini)" + "\n ",
  )
  subparser_setup.add_argument(
    "--cluster",
    action="store_true",
    help="to generate files for running on cluster" + "\n ",
  )
  subparser_setup.add_argument(
    "--animate",
    action="store_true",
    help="flag to create movie file from simulation results" + "\n ",
  )
  subparser_setup.add_argument(
    "--execute",
    action="store_true",
    help="to start simulations using generated files" + "\n ",
  )
  subparser_setup.set_defaults(call=call_liggghts_setup)

  # parser for liggghts execute function
  subparser_execute = subparsers_liggghts.add_parser(
    "execute",
    formatter_class=argparse.RawTextHelpFormatter,
    help="command for executing simulation",
    description="command 'liggghts execute': to execute simulation\n\n"
    + "required argument is ini file (**.ini. '--ini').\n\n"
    + "(see sub-option 'vibpump liggghts execute -h')\n",
  )
  subparser_execute.add_argument(
    "--ini",
    nargs="*",
    type=str,
    metavar="path",
    help="path to ini file (**.ini)" + "\n ",
  )
  subparser_execute.add_argument(
    "--cluster",
    action="store_true",
    help="flag to execute simulation on cluster" + "\n ",
  )
  subparser_execute.set_defaults(call=call_liggghts_execute)

  # parser for liggghts copy function
  subparser_copy = subparsers_liggghts.add_parser(
    "copy",
    formatter_class=argparse.RawTextHelpFormatter,
    help="command for copying simulation (or post-process) results",
    description="command 'liggghts copy': to copy simulation results\n\n"
    + "required argument is ini file (**.ini. '--ini').\n"
    + "default: to copy movie .mp4 file into gsync directory file.\n\n"
    + "(see sub-option 'vibpump liggghts copy -h')\n",
  )
  subparser_copy.add_argument(
    "--ini",
    nargs="*",
    type=str,
    metavar="path",
    help="path to ini file (**.ini)" + "\n ",
  )
  subparser_copy.add_argument(
    "--logSim", action="store_true", help="flag to copy log of simulation" + "\n ",
  )
  subparser_copy.add_argument(
    "--logPost", action="store_true", help="flag to copy log of post-process" + "\n ",
  )
  subparser_copy.set_defaults(call=call_liggghts_copy)

  # parser for liggghts log function
  subparser_log = subparsers_liggghts.add_parser(
    "log",
    formatter_class=argparse.RawTextHelpFormatter,
    help="command for showing simulation (or post-process) log",
    description="command 'liggghts log': to show log\n\n"
    + "required argument is ini file (**.ini. '--ini').\n"
    + "default: to show 15 lines of tail part of simulation log file.\n\n"
    + "(see sub-option 'vibpump liggghts log -h')\n",
  )
  subparser_log.add_argument(
    "--ini",
    nargs="*",
    type=str,
    metavar="path",
    help="path to ini file (**.ini)" + "\n ",
  )
  subparser_log.add_argument(
    "--head", action="store_true", help="flag to show head part of log file" + "\n ",
  )
  subparser_log.add_argument(
    "--process", action="store_true", help="flag to show post-process log file" + "\n ",
  )
  subparser_log.add_argument(
    "--line",
    type=int,
    metavar="line",
    default=None,
    help="how many lines of log file to be shown (default: 15)" + "\n ",
  )
  subparser_log.set_defaults(call=call_liggghts_log)

  # parser for liggghts process function
  subparser_process = subparsers_liggghts.add_parser(
    "process",
    formatter_class=argparse.RawTextHelpFormatter,
    help="command for post-process of simulation",
    description="command 'liggghts process': post-process of simulation\n\n"
    + "basic required arguments is ini file (**.ini. '--ini').\n\n"
    + "(see sub-option 'vibpump liggghts process -h')\n",
  )
  subparser_process.add_argument(
    "--ini",
    nargs="*",
    type=str,
    metavar="path",
    help="path to ini file (**.ini)" + "\n ",
  )
  subparser_process.add_argument(
    "--cluster",
    action="store_true",
    help="flag to generate post-process files for running on cluster" + "\n ",
  )
  subparser_process.add_argument(
    "--animate",
    action="store_true",
    help="to create movie from simulation results" + "\n ",
  )
  subparser_process.add_argument(
    "--fps",
    type=int,
    metavar="fps",
    help="fps when to create movie file from simulation results" + "\n ",
  )
  subparser_process.add_argument(
    "--measureHeight",
    action="store_true",
    help="to measure climbing height from simulation results" + "\n ",
  )
  subparser_process.add_argument(
    "--graphHeight",
    action="store_true",
    help="to graph climbing height results" + "\n ",
  )
  subparser_process.set_defaults(call=call_liggghts_process)

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
