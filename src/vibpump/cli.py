"""cli command for supporting vibpump projects.

Experiments:
Basic required arguments is movie name and process name. if no movie and process is given, error will be raised.

Output data (after image process) will be generated in 'cv2/target-noExtension/process-name/target' directory under current location (e.g. (test.mp4) ./cv2/test/binarized/test.png).

Simulation:
This supports LIGGGHTS simulations.

see usage '-h option'

"""
import argparse
import sys
from typing import List
from imgproc import api
from imgproc import process


class AnimateAction(argparse.Action):
  def __call__(self, parser, namespace, values, option_string=None):

    para_dict = {"is_colored": False, "fps": 20.0}

    for value in values:
      s = value.split("=")
      if len(s) == 2:

        if s[0] == "is_colored" and (s[1] == "False" or "True"):
          para_dict["is_colored"] = True if s[1] == "True" else False

        if s[0] == "fps":
          para_dict["fps"] = float(s[1])

    setattr(namespace, self.dest, para_dict)


class BinarizeAction(argparse.Action):
  def __call__(self, parser, namespace, values, option_string=None):

    para_dict = {}

    # for value in values:
    #   s = value.split("=")
    #   if len(s) == 2:

    #     if s[0] == "is_colored" and (s[1] == "False" or "True"):
    #       para_dict["is_colored"] = True if s[1] == "True" else False

    #     if s[0] == "fps":
    #       para_dict["fps"] = float(s[1])

    setattr(namespace, self.dest, para_dict)


def read_cli_argument() -> List[process.ABCProcess]:
  """read and parse cli arguments

  Returns:
      List[process.ABCProcess]: list of sub-class of ABCProcess class
  """
  parser = argparse.ArgumentParser(
    prog="vibpump.py",
    formatter_class=argparse.RawTextHelpFormatter,
    description="python package providing functions for vibpump project."
    + "\noutput for experiment is generated in 'cv2' directory under current location.",
  )

  parser.add_argument(
    "--movie", nargs="*", type=str, metavar="path", help="movie path" + "\n ",
  )
  parser.add_argument(
    "--animate",
    nargs="*",
    type=str,
    metavar="dict",
    action=AnimateAction,
    help="is_colored=False fps=20.0 path of picture or directory where pictures are stored"
    + "\nIf directory name is given,"
    + "same process will be applied to all pictures in the directory"
    + "\n ",
  )
  parser.add_argument(
    "--binarize",
    nargs="*",
    type=str,
    metavar="dict",
    action=BinarizeAction,
    help="is_colored=False fps=20.0 path of picture or directory where pictures are stored"
    + "\nIf directory name is given,"
    + "same process will be applied to all pictures in the directory"
    + "\n ",
  )

  if len(sys.argv) <= 1:
    sys.exit(parser.format_help())

  args = parser.parse_args()
  print(args)

  if not args.movie:
    sys.exit("no movie is given!")

  if type(args.animate) is dict:
    print(args.animate)

  if type(args.binarize) is dict:
    print(args.binarize)

  # return args.call(args, parser)


def main() -> None:
  """cli command main function
  """
  read_cli_argument()
  # image_process.execute()


if __name__ == "__main__":
  main()
