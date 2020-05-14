"""liggghts module containing support functions for simulations
"""
# import csv
# import cv2
# import inspect
# import numpy
# import math
import pathlib
import shutil

# import re
# from matplotlib import pyplot
from typing import List, Tuple


def create_jobs(ini_list: List[str], is_cluster: bool = False):
  """create each job for simulation

  Args:
      ini_list (List[str]): list of iniFile files
  """
  for ini in ini_list:

    jobs, parameters, clusters = read_ini_file(ini)
    if not check_parameters(ini, jobs, parameters):
      continue
    np = get_parallel_size_list(jobs, parameters)

    if is_cluster:
      if not check_cluster_parameters(ini, jobs, clusters, np):
        continue

    home_path = pathlib.Path(pathlib.Path.home())
    sim_path = pathlib.Path(pathlib.Path.cwd() / pathlib.Path(ini).stem)
    sim_path.mkdir(parents=True, exist_ok=True)

    with open(pathlib.Path(sim_path / "job_exe.sh"), "w") as f:
      f.write("#!/bin/bash\n\n")
    if is_cluster:
      with open(pathlib.Path(sim_path / "qsub_exe.sh"), "w") as f:
        f.write("#!/bin/bash\n\n")

    for idx, job in enumerate(jobs):

      job_dir_path = pathlib.Path(sim_path / job)
      script = str(pathlib.Path(job_dir_path / "ini.script"))
      job_sh = str(pathlib.Path(job_dir_path / "job.sh"))
      lmp = str(home_path) + "/local/bin/lmp_auto"

      if not job_dir_path.is_dir():
        job_dir_path.mkdir(parents=True)
      elif list(job_dir_path.iterdir()):
        shutil.rmtree(job_dir_path)
        job_dir_path.mkdir(parents=True)

      with open(script, "w") as f:
        for parameter in parameters:
          if len(parameter) == 1:
            f.write(parameter[0] + "\n")
          else:
            f.write(parameter[idx] + "\n")

      with open(pathlib.Path(sim_path / "job_exe.sh"), "a") as f:
        f.write("cd " + str(job_dir_path) + "\nbash " + job_sh + "\n")

      with open(job_sh, "w") as f:
        f.write("#!/bin/bash\n\n")
        f.write("mpirun -np {0} {1} < {2}".format(np[idx], lmp, script) + "\n")

      if not is_cluster:
        continue
      hostfile = str(pathlib.Path(job_dir_path / "hostfile"))
      qsub_sh = str(pathlib.Path(job_dir_path / "qsub.sh"))
      vtk_lib = str(home_path) + "/build/LIGGGHTS-PUBLIC/lib/vtk/install/lib"
      openmpi = "/usr/mpi/gcc/openmpi-1.10.5a1/bin/mpirun"

      with open(hostfile, "w") as f:
        for host in clusters[idx].split("+"):
          f.write(host.strip() + "\n")

      with open(pathlib.Path(sim_path / "qsub_exe.sh"), "a") as f:
        f.write("cd " + str(job_dir_path) + "\nqsub " + qsub_sh + "\n")

      with open(qsub_sh, "w") as f:
        f.write("#!/bin/bash\n\n")
        f.write("#$ -cwd\n")
        f.write("#$ -N liggghts\n")
        f.write("#$ -o stdout\n")
        f.write("#$ -e stderr\n")
        f.write("#$ -M Masato.Adachi@dlr.de\n")
        f.write("#$ -m ae\n\n")
        f.write(openmpi)
        f.write(" -x LD_LIBRARY_PATH=$LD_LIBRARY_PATH:" + vtk_lib)
        f.write(" -x HCOLL_ENABLE_MCAST_ALL=0")
        f.write(" -np " + str(np[idx]))
        f.write(" --hostfile " + hostfile)
        f.write(" --mca opal_event_include poll")
        f.write(" --mca orte_base_help_aggregate 0")
        f.write(" --mca btl_openib_warn_default_gid_prefix to 0")
        f.write(' bash -c "ulimit -s 10240 && ' + lmp + " < " + script + '"\n')


def read_ini_file(ini: str) -> Tuple[List[str], List[List[str]], List[str]]:
  """read iniFile

  Args:
      ini_list (List[str]): list of ini files

  Returns:
      Tuple[List[str], List[List[str]], List[str]]: jobs, parameters, cluster_parameters
  """
  is_job = False
  is_parameter_set = False
  is_cluster = False
  jobs: List[str] = []
  parameter: List[str] = []
  parameters: List[List[str]] = []
  clusters: List[str] = []

  with open(ini) as f:
    for line in f:
      stripped = line.strip()
      if not stripped:
        continue
      if stripped[0] == "#":
        continue
      if stripped[0] == "%":
        is_job = False
        is_parameter_set = False
        is_cluster = False
        if parameter:
          parameters.append(parameter.copy())
          parameter.clear()
        if "%job" in stripped:
          is_job = True
          continue
        if "%param" in stripped:
          parameters.append([stripped.replace("%param", "").strip()])
          continue
        if "%set_param" in stripped:
          is_parameter_set = True
          continue
        if "%set_cluster" in stripped:
          is_cluster = True
          continue

      if is_job:
        jobs.append(stripped)
      if is_parameter_set:
        parameter.append(stripped)
      if is_cluster:
        clusters.append(stripped)

  if parameter:
    parameters.append(parameter.copy())

  return jobs, parameters, clusters


def check_parameters(ini: str, jobs: List[str], parameters: List[List[str]]) -> bool:
  """check if ini file inputs are correct

  Args:
      ini (str): ini files
      jobs (List[str]): jobs
      parameters (List[List[str]]): parameters

  Returns:
      bool: if inputs are correct (true:correct)
  """
  if not jobs:
    print("{0}: no job is given!".format(ini))
    return False
  if len(set(jobs)) != len(jobs):
    print("{0}: same job name exists!".format(ini))
    return False
  if " " in "".join(jobs):
    print("{0}: whitespace exists in job name!".format(ini))
    return False
  if not parameters:
    print("{0}: no parameter is given!".format(ini))
    return False

  unmatched = [p for p in parameters if not ((len(p) == len(jobs)) or (len(p) == 1))]
  if unmatched:
    print("{0}\n{1}: parameter size is wrong!".format(unmatched, ini))
    return False

  cad = ["cad" for job in jobs]
  for parameter in parameters:
    if not [p for p in parameter if "mesh/surface file " in p]:
      continue

    if len(parameter) == 1:
      v = parameter[0].split()
      cad_file = v[v.index("file") + 1]
      parameter[0] = parameter[0].replace(
        "file {0}".format(cad_file),
        "file {0}".format(str(pathlib.Path(cad_file).resolve())),
      )
      for idx in range(len(cad)):
        cad[idx] = cad_file
    else:
      for idx in range(len(cad)):
        v = parameter[idx].split()
        cad_file = v[v.index("file") + 1]
        cad[idx] = cad_file
        parameter[idx] = parameter[idx].replace(
          "file {0}".format(cad_file),
          "file {0}".format(str(pathlib.Path(cad_file).resolve())),
        )

  if [c for c in cad if not pathlib.Path(c).is_file()]:
    print("{0}\n{1}: cad file does not exist!".format(cad, ini))
    return False

  return True


def check_cluster_parameters(
  ini: str, jobs: List[str], clusters: List[str], np: List[int]
) -> bool:
  """check if ini file inputs are correct

  Args:
      ini (str): ini files
      jobs (List[str]): jobs
      clusters (List[str]): cluster parameters
      no (List[int]): list of parallel process sizes

  Returns:
      bool: if inputs are correct (true:correct)
  """
  if not clusters:
    print("{0}: no cluster parameter is given!".format(ini))
    return False

  if len(clusters) != len(jobs):
    print("{0}\n{1}: cluster parameter size is wrong!".format(clusters, ini))
    return False

  cnp = [1 for cluster in clusters]
  for idx, cluster in enumerate(clusters):
    cnp[idx] = sum([int(c.split("=")[1]) for c in cluster.split() if "slots=" in c])
  if np != cnp:
    print("ini: {0}\nhost: {1}\n: parallel process size is wrong!".format(np, cnp))
    return False

  return True


def get_parallel_size_list(jobs: List[str], parameters: List[List[str]]) -> List[int]:
  """get list of parallel process sizes

  Args:
      jobs (List[str]): jobs
      parameters (List[List[str]]): parameters

  Returns:
      List[int]: list of parallel process sizes
  """
  np = [1 for job in jobs]

  for parameter in parameters:
    if not [p for p in parameter if "processors" in p]:
      continue

    if len(parameter) == 1 and [n for n in parameter[0].split() if n.isnumeric()]:
      for idx in range(len(np)):
        np[idx] = sum([int(n) for n in parameter[0].split() if n.isnumeric()])
    else:
      for idx, p in enumerate(parameter):
        if [n for n in p.split() if n.isnumeric()]:
          np[idx] = sum([int(n) for n in p.split() if n.isnumeric()])

  return np
