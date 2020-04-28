"""image module containing image process functions
"""
import numpy
import matplotlib
import pathlib
from typing import List, Tuple


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


def graph(target_list: List[str]) -> List[str]:
  """graph measured height

  Args:
      target_list (List[str]): list of measured climbing height data of movie

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


def measure(target_list: List[str], movie_list: List[str]) -> List[str]:
  """measure climbing height (this require binarized data)

  Args:
      target_list (List[str]): list of measured climbing height data of movie
      movie_list (List[str]): list of movie

  Returns:
      List[str]: list of input
  """
  path_list: List[str] = []
  cv2_path = pathlib.Path(pathlib.Path.cwd() / "cv2")

  for movie in movie_list:
    movie_path = pathlib.Path(movie)
    input_path = pathlib.Path(cv2_path / movie_path.stem / "binarized")

    if input_path.is_dir():
      for target in target_list:
        if str(input_path) == target:
          path_list.append(str(input_path))
    else:
      print("'{0}' does not exist!".format(str(input_path)))

  print(path_list)
