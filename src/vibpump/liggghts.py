"""liggghts module containing support functions for simulations
"""
# import csv
# import inspect
# import numpy
import math
import pathlib
import re
import shutil
import subprocess

# from matplotlib import pyplot
from typing import List, TextIO, Tuple


def read_ini_file(ini: str) -> Tuple[List[str], List[List[str]], List[str], List[int]]:
  """read ini file

  Args:
      ini (str): ini file

  Returns:
      Tuple[List[str], List[List[str]], List[str], List[int]]: jobs, parameters, cluster_parameters, numbers of parallel-processes
  """
  is_job, is_parameter, is_cluster = False, False, False
  jobs: List[str] = []
  parameter: List[str] = []
  parameters: List[List[str]] = []
  clusters: List[str] = []
  np: List[int] = []

  with open(ini) as f:

    for line in f:
      stripped = line.strip()

      if not stripped:
        continue
      if stripped[0] == "#":
        continue

      if stripped[0] == "%":
        is_job, is_parameter, is_cluster = False, False, False

        if parameter:
          parameters.append(parameter.copy())
          parameter.clear()

        if "%param" in stripped:
          parameters.append([stripped.replace("%param", "").strip()])
          continue

        if "%set_job" in stripped:
          is_job = True
          continue
        if "%set_param" in stripped:
          is_parameter = True
          continue
        if "%set_cluster" in stripped:
          is_cluster = True
          continue

      if is_job:
        jobs.append(stripped)
        np.append(1)
      if is_parameter:
        parameter.append(stripped)
      if is_cluster:
        clusters.append(stripped)

  if parameter:
    parameters.append(parameter.copy())

  for parameter in parameters:

    if not [p for p in parameter if "processors" in p]:
      continue

    if len(parameter) == 1:
      if [n for n in parameter[0].split() if n.isnumeric()]:
        for idx in range(len(np)):
          np[idx] = math.prod([int(n) for n in parameter[0].split() if n.isnumeric()])
    else:
      for idx, p in enumerate(parameter):
        if [n for n in p.split() if n.isnumeric()]:
          np[idx] = math.prod([int(n) for n in p.split() if n.isnumeric()])

  return jobs, parameters, clusters, np


def check_parameters(ini: str, jobs: List[str], parameters: List[List[str]]) -> bool:
  """check if ini file inputs are correct

  Args:
      ini (str): ini file
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
    print("{0}: parameter size is wrong!\n{1}\n".format(ini, unmatched))
    return False

  for parameter in parameters:

    if not [p for p in parameter if "mesh/surface file " in p]:
      continue

    if len(parameter) == 1:
      splitted = parameter[0].split()
      cad_file_path = pathlib.Path(splitted[splitted.index("file") + 1])
      if not cad_file_path.is_file():
        print("{0}: cad file does not exist!\n{1}\n".format(ini, str(cad_file_path)))
        return False
      parameter[0] = parameter[0].replace(
        "file {0}".format(str(cad_file_path)),
        "file {0}".format(str(cad_file_path.resolve())),
      )
    else:
      for idx in range(len(parameter)):
        splitted = parameter[idx].split()
        cad_file_path = pathlib.Path(splitted[splitted.index("file") + 1])
        if not cad_file_path.is_file():
          print("{0}: cad file does not exist!\n{1}\n".format(ini, str(cad_file_path)))
          return False
        parameter[idx] = parameter[idx].replace(
          "file {0}".format(str(cad_file_path)),
          "file {0}".format(str(cad_file_path.resolve())),
        )

  return True


def check_cluster_parameters(
  ini: str, jobs: List[str], clusters: List[str], np: List[int]
) -> bool:
  """check if ini file inputs are correct

  Args:
      ini (str): ini file
      jobs (List[str]): jobs
      clusters (List[str]): cluster parameters
      np (List[int]): list of parallel process numbers

  Returns:
      bool: if inputs are correct (true:correct)
  """
  if not clusters:
    print("{0}: no cluster parameter is given!".format(ini))
    return False

  if len(clusters) != len(jobs):
    print("{0}: cluster parameter size is wrong!\n{1}\n".format(ini, clusters))
    return False

  cnp = [1 for cluster in clusters]

  for idx, cluster in enumerate(clusters):
    cnp[idx] = sum([int(c.split("=")[1]) for c in cluster.split() if "slots=" in c])

  if np != cnp:
    print("{0}: parallel process size is not equal!\n".format(ini))
    print("processors: {0}\nhostfile: {1}\n".format(np, cnp))
    return False

  return True


def execute_sh(script: str) -> bool:
  """execute script

  Args:
      script (str): script file

  Returns:
      bool: if script is executed (true:executed)
  """
  if pathlib.Path(script).is_file():
    subprocess.run(["bash", script])
    return True
  else:
    print("'{0}' does not exists!".format(script))
    return False


def setup(
  ini_list: List[str],
  is_cluster: bool = False,
  is_animated: bool = False,
  is_executed: bool = False,
):
  """create liggghts simulation scripts

  Args:
      ini_list (List[str]): list of ini files
      is_cluster (bool): flag to apply for cluster job
      is_animated (bool): flag to apply animate process
      is_executed (bool): flag to execute simulation
  """
  for ini in ini_list:

    jobs, parameters, clusters, parallels = read_ini_file(ini)

    if not check_parameters(ini, jobs, parameters):
      continue
    if is_cluster and (not check_cluster_parameters(ini, jobs, clusters, parallels)):
      continue

    jobs_dir = str(pathlib.Path(pathlib.Path.cwd() / pathlib.Path(ini).stem))
    pathlib.Path(jobs_dir).mkdir(parents=True, exist_ok=True)
    qsub_exe_all_sh = jobs_dir + "/qsub_exe_all.sh"
    exe_all_sh = jobs_dir + "/exe_all.sh"

    home = str(pathlib.Path.home().resolve())
    vtk = home + "/build/LIGGGHTS-PUBLIC/lib/vtk/install/lib"
    lmp = home + "/build/LIGGGHTS-PUBLIC/src/lmp_auto"
    stdout = jobs_dir + "/stdout_exe"
    stderr = jobs_dir + "/stderr_exe"
    open(stdout, "w").close()
    open(stderr, "w").close()

    if is_cluster:
      with open(qsub_exe_all_sh, "w") as f:
        f.write("#!/bin/bash\n\n")
        f.write("#$ -cwd\n")
        f.write("#$ -N {0}\n".format(ini))
        f.write("#$ -t 1-{0}\n".format(str(len(jobs))))
        f.write("#$ -o {0}\n".format(stdout))
        f.write("#$ -e {0}\n".format(stderr))
        f.write("#$ -M Masato.Adachi@dlr.de\n")
        f.write("#$ -m es\n\n")

        f.write("NP_LIST=( ")
        for np in parallels:
          f.write('"{0}" '.format(str(np)))
        f.write(")\n\n")

        f.write("DIR_LIST=( ")
        for idx, job in enumerate(jobs):
          job_dir = str(pathlib.Path(jobs_dir + "/" + job))
          f.write('"{0}" '.format(job_dir))
        f.write(")\n\n")

        f.write("HOST_LIST=( ")
        for idx, job in enumerate(jobs):
          job_dir = str(pathlib.Path(jobs_dir + "/" + job))
          hostfile = job_dir + "/hostfile"
          f.write('"{0}" '.format(hostfile))
        f.write(")\n\n")

        f.write("INI_LIST=( ")
        for idx, job in enumerate(jobs):
          job_dir = str(pathlib.Path(jobs_dir + "/" + job))
          ini_script = job_dir + "/ini.script"
          f.write('"{0}" '.format(ini_script))
        f.write(")\n\n")

        f.write("NP=NP_LIST[$SGE_TASK_ID]\n")
        f.write("DIR=DIR_LIST[$SGE_TASK_ID]\n")
        f.write("HOST=HOST_LIST[$SGE_TASK_ID]\n")
        f.write("INI=INI_LIST[$SGE_TASK_ID]\n")

        f.write("/usr/mpi/gcc/openmpi-1.10.5a1/bin/mpirun")
        f.write(" -x LD_LIBRARY_PATH=$LD_LIBRARY_PATH:{0}".format(vtk))
        f.write(" -np $NP")
        f.write(" --hostfile $HOST")
        f.write(" --mca opal_event_include poll")
        f.write(" --mca orte_base_help_aggregate 0")
        f.write(" --mca btl_openib_warn_default_gid_prefix 0")
        f.write(' bash -c "ulimit -s 10240 && cd $DIR && ')
        f.write('{0} < $INI"\n\n'.format(lmp))

    # with open(qsub_exe_all_sh if is_cluster else exe_all_sh, "w") as f:
    #   f.write("#!/bin/bash\n\n")

    for idx, job in enumerate(jobs):

      job_dir = str(pathlib.Path(jobs_dir + "/" + job))
      if pathlib.Path(job_dir).is_dir():
        shutil.rmtree(job_dir)

      pathlib.Path(job_dir).mkdir(parents=True)
      np = parallels[idx]
      home = str(pathlib.Path.home().resolve())
      lmp = home + "/build/LIGGGHTS-PUBLIC/src/lmp_auto"
      ini_script = job_dir + "/ini.script"

      with open(ini_script, "w") as f:
        for parameter in parameters:
          f.write(parameter[0] + "\n" if len(parameter) == 1 else parameter[idx] + "\n")

      if is_cluster:

        qsub_exe_sh = job_dir + "/qsub_exe.sh"
        hostfile = job_dir + "/hostfile"

        stdout = job_dir + "/stdout_exe"
        stderr = job_dir + "/stderr_exe"
        open(stdout, "w").close()
        open(stdout, "w").close()

        # with open(qsub_exe_sh, "w") as f:
        #   f.write("#!/bin/bash\n\n")
        #   f.write("#$ -cwd\n")
        #   f.write("#$ -N {0}\n".format(job))
        #   f.write("#$ -o {0}\n".format(stdout))
        #   f.write("#$ -e {0}\n".format(stderr))
        #   f.write("#$ -M Masato.Adachi@dlr.de\n")
        #   f.write("#$ -m es\n\n")
        #   f.write("/usr/mpi/gcc/openmpi-1.10.5a1/bin/mpirun")
        #   f.write(" -x LD_LIBRARY_PATH=$LD_LIBRARY_PATH:{0}".format(vtk))
        #   f.write(" -np {0}".format(str(np)))
        #   f.write(" --hostfile {0}".format(hostfile))
        #   f.write(" --mca opal_event_include poll")
        #   f.write(" --mca orte_base_help_aggregate 0")
        #   f.write(" --mca btl_openib_warn_default_gid_prefix 0")
        #   f.write(' bash -c "ulimit -s 10240 && {0} < {1}"\n\n'.format(lmp, ini_script))
        #   if is_animated:
        #     add_animate_process(job_dir, np, f, is_cluster)

        with open(hostfile, "w") as f:
          for host in clusters[idx].split("+"):
            f.write(host.strip() + "\n")

      else:

        exe_sh = job_dir + "/exe.sh"

        with open(exe_all_sh, "a") as f:
          f.write("cd {0}\n".format(job_dir))
          f.write("bash {0}\n\n".format(exe_sh))

        with open(exe_sh, "w") as f:
          f.write("#!/bin/bash\n\n")
          f.write("mpirun -np {0} {1} < {2}\n\n".format(np, lmp, ini_script))
          if is_animated:
            add_animate_process(job_dir, np, f, is_cluster)

    if is_executed:
      execute_sh(qsub_exe_all_sh) if is_cluster else execute_sh(exe_all_sh)


def execute(ini_list: List[str], is_cluster: bool = False):
  """execute liggghts simulation

  Args:
      ini_list (List[str]): list of ini files
      is_cluster (bool): flag to apply for cluster job
  """
  for ini in ini_list:

    jobs_dir = str(pathlib.Path(pathlib.Path.cwd() / pathlib.Path(ini).stem))
    qsub_exe_all_sh = jobs_dir + "/qsub_exe_all.sh"
    exe_all_sh = jobs_dir + "/exe_all.sh"
    execute_sh(qsub_exe_all_sh) if is_cluster else execute_sh(exe_all_sh)


def post_process(ini_list: List[str], is_cluster: bool = False):
  """post-process of liggghts simulation

  Args:
      ini_list (List[str]): list of ini files
      is_cluster (bool): flag to apply for cluster job
  """
  pass
  # for ini in ini_list:

  #   jobs, parameters, clusters, parallels = read_ini_file(ini)
  #   jobs_dir = str(pathlib.Path(pathlib.Path.cwd() / pathlib.Path(ini).stem))
  #   qsub_exe_all_sh = jobs_dir + "/qsub_exe_all.sh"
  #   exe_all_sh = jobs_dir + "/exe_all.sh"

  #   with open(qsub_exe_all_sh if is_cluster else exe_all_sh, "w") as f:
  #     f.write("#!/bin/bash\n\n")

  #   for idx, job in enumerate(jobs):

  #     job_dir = str(pathlib.Path(jobs_dir + "/" + job))
  #     if not pathlib.Path(job_dir).is_dir():
  #       continue

  #     np = parallels[idx]
  #     home = str(pathlib.Path.home().resolve())

  #     if is_cluster:

  #       qsub_exe_sh = job_dir + "/qsub_exe.sh"
  #       hostfile = job_dir + "/hostfile"
  #       vtk = home + "/build/LIGGGHTS-PUBLIC/lib/vtk/install/lib"

  #       with open(qsub_exe_all_sh, "a") as f:
  #         f.write("cd {0}\n".format(job_dir))
  #         f.write("qsub {0}\n\n".format(qsub_exe_sh))

  #       with open(qsub_exe_sh, "w") as f:
  #         f.write("#!/bin/bash\n\n")
  #         f.write("#$ -cwd\n")
  #         f.write("#$ -N {0}\n".format(job))
  #         f.write("#$ -o {0}\n".format(job_dir + "/stdout.exe"))
  #         f.write("#$ -e {0}\n".format(job_dir + "/stderr.exe"))
  #         f.write("#$ -M Masato.Adachi@dlr.de\n")
  #         f.write("#$ -m es\n\n")
  #         f.write("/usr/mpi/gcc/openmpi-1.10.5a1/bin/mpirun")
  #         f.write(" -x LD_LIBRARY_PATH=$LD_LIBRARY_PATH:{0}".format(vtk))
  #         f.write(" -np {0}".format(str(np)))
  #         f.write(" --hostfile {0}".format(hostfile))
  #         f.write(" --mca opal_event_include poll")
  #         f.write(" --mca orte_base_help_aggregate 0")
  #         f.write(" --mca btl_openib_warn_default_gid_prefix 0")
  #         f.write(' bash -c "ulimit -s 10240 && {0} < {1}"\n\n'.format(lmp, ini_script))
  #         if is_animated:
  #           add_animate_process(job_dir, np, f, is_cluster)

  #     else:

  #       exe_sh = job_dir + "/exe.sh"

  #       with open(exe_all_sh, "a") as f:
  #         f.write("cd {0}\n".format(job_dir))
  #         f.write("bash {0}\n\n".format(exe_sh))

  #       with open(exe_sh, "w") as f:
  #         f.write("#!/bin/bash\n\n")
  #         f.write("mpirun -np {0} {1} < {2}\n\n".format(np, lmp, ini_script))
  #         if is_animated:
  #           add_animate_process(job_dir, np, f, is_cluster)

  #   if is_executed:
  #     execute_sh(qsub_exe_all_sh) if is_cluster else execute_sh(exe_all_sh)


def add_animate_process(job_dir: str, np: int, IO: TextIO, is_cluster: bool = False):
  """add animate process description

  Args:
      job_dir (str): job directory name
      np (int): parallel number
      IO (io.TextIO): file object
      is_cluster (bool): flag to apply for cluster job
  """
  if not [pathlib.Path(job_dir + "/post").iterdir()]:
    print("no file exists in '{0}'!".format(job_dir + "/post"))
    return

  animate_dir = job_dir + "/animate"
  if pathlib.Path(animate_dir).is_dir():
    shutil.rmtree(animate_dir)

  pathlib.Path(animate_dir).mkdir(parents=True)
  pvbatch_py = animate_dir + "/pvbatch.py"
  animate_py = animate_dir + "/animate.py"
  write_pvbatch_py(job_dir, pvbatch_py)
  write_animate_py(job_dir, animate_py)

  pvbatch = str(pathlib.Path.home().resolve()) + "/local/bin/pvbatch"
  pvbatch_lib = str(pathlib.Path.home().resolve()) + "/local/lib"
  py38 = str(pathlib.Path.home().resolve()) + "/local/bin/python3.8"

  if is_cluster:

    IO.write("/usr/mpi/gcc/openmpi-1.10.5a1/bin/mpirun")
    IO.write(" -x LD_LIBRARY_PATH=$LD_LIBRARY_PATH:{0}".format(pvbatch_lib))
    IO.write(" -np {0}".format(np))
    IO.write(" --hostfile {0}".format(job_dir + "/hostfile"))
    IO.write(" --mca opal_event_include poll")
    IO.write(" --mca orte_base_help_aggregate 0")
    IO.write(" --mca btl_openib_warn_default_gid_prefix 0")
    IO.write(
      ' bash -c "ulimit -s 10240 && {0} --use-offscreen-rendering {1}"\n\n'.format(
        pvbatch, pvbatch_py
      )
    )
    IO.write("{0} {1}\n\n".format(py38, animate_py))

  else:

    IO.write("#!/bin/bash\n\n")
    IO.write(
      "mpirun -np {0} pvbatch --use-offscreen-rendering {1}\n\n".format(np, pvbatch_py)
    )
    IO.write("{0} {1}\n\n".format(py38, animate_py))


def write_pvbatch_py(job_dir: str, pvbatch_py: str):
  """write pvbatch.py file

  Args:
      job_dir (str): job directory name
      pvbatch_py (str): pvbatch.py file
  """
  post_path = pathlib.Path(job_dir + "/post")
  particles = [
    str(p) for p in list(post_path.glob("**/p_*.vtk")) if "bounding" not in str(p)
  ]
  cads = [str(c) for c in post_path.glob("**/cad_*.vtk")]
  boxes = [str(b) for b in post_path.glob("**/*bounding*.vtk")]

  match = re.compile(r"\d+")
  particles.sort(key=lambda s: int(match.findall(s)[-1]))
  cads.sort(key=lambda s: int(match.findall(s)[-1]))
  boxes.sort(key=lambda s: int(match.findall(s)[-1]))

  with open(pvbatch_py, "w") as f:

    f.write("from paraview.simple import *\n\n")
    f.write("paraview.simple._DisableFirstRenderCameraReset()\n")

    f.write("p_ = LegacyVTKReader(FileNames=[\n")
    for particle in particles:
      f.write('  "{0}",\n'.format(particle))
    f.write("])\n\n")

    f.write("cad_ = LegacyVTKReader(FileNames=[\n")
    for cad in cads:
      f.write('  "{0}",\n'.format(cad))
    f.write("])\n\n")

    f.write("p_boundingBox_ = LegacyVTKReader(FileNames=[\n")
    for box in boxes:
      f.write('  "{0}",\n'.format(box))
    f.write("])\n\n")

    f.write("animationScene1 = GetAnimationScene()\n")
    f.write("animationScene1.UpdateAnimationUsingDataTimeSteps()\n")
    f.write('renderView1 = GetActiveViewOrCreate("RenderView")\n\n')

    f.write("p_Display = Show(p_, renderView1)\n")
    f.write('p_Display.Representation = "Surface"\n\n')

    f.write("cad_Display = Show(cad_, renderView1)\n")
    f.write('cad_Display.Representation = "Surface"\n\n')

    f.write("p_boundingBox_Display = Show(p_boundingBox_, renderView1)\n")
    f.write('p_boundingBox_Display.Representation = "Outline"\n\n')

    f.write('glyph1 = Glyph(Input=p_, GlyphType="Sphere")\n')
    f.write('glyph1.Scalars = ["POINTS", "radius"]\n')
    f.write('glyph1.Vectors = ["POINTS", "None"]\n')
    f.write('glyph1.ScaleMode = "scalar"\n')
    f.write("glyph1.ScaleFactor = 2.0\n")
    f.write('glyph1.GlyphMode = "All Points"\n')
    f.write("glyph1Display = Show(glyph1, renderView1)\n")
    f.write('glyph1Display.Representation = "Surface"\n')
    f.write("Hide(p_, renderView1)\n\n")

    f.write("clip1 = Clip(Input=glyph1)\n")
    f.write('clip1.ClipType = "Plane"\n')
    f.write("clip1.ClipType.Origin = [0.0, 0.0, 0.0]\n")
    f.write("clip1.ClipType.Normal = [0.0, 1.0, 0.0]\n")
    f.write("clip1Display = Show(clip1, renderView1)\n")
    f.write('clip1Display.Representation = "Surface"\n')
    f.write("Hide(glyph1, renderView1)\n\n")

    f.write("clip2 = Clip(Input=cad_)\n")
    f.write('clip2.ClipType = "Plane"\n')
    f.write("clip2.ClipType.Origin = [0.0, 0.0, 0.0]\n")
    f.write("clip2.ClipType.Normal = [0.0, 1.0, 0.0]\n")
    f.write("clip2Display = Show(clip2, renderView1)\n")
    f.write('clip2Display.Representation = "Surface"\n')
    f.write("Hide(cad_, renderView1)\n\n")

    f.write("annotateTimeFilter1 = AnnotateTimeFilter(Input=clip2)\n")
    f.write('annotateTimeFilter1.Format = "Step: %.0f"\n')
    f.write("annotateTimeFilter1Display = Show(annotateTimeFilter1, renderView1)\n\n")

    f.write("renderView1.Update()\n")
    f.write("SetActiveSource(None)\n")
    f.write("renderView1.CameraPosition = [0.0, -0.5, 0.09]\n")
    f.write("renderView1.CameraFocalPoint = [0.0, 0.0, 0.09]\n")
    f.write("renderView1.CameraViewUp = [0.0, 0.0, 1.0]\n")
    f.write("renderView1.CameraParallelScale = 0.12\n\n")

    f.write("SaveAnimation(\n")
    f.write('  "{0}/animate/p_.png",\n'.format(job_dir))
    f.write("  renderView1,\n")
    f.write("  ImageResolution=[480, 640],\n")
    f.write("  FrameWindow=[0, {0}]\n".format(str(len(particles))))
    f.write(")\n\n")


def write_animate_py(job_dir: str, animate_py: str, fps: float = 10):
  """write animate.py file

  Args:
      job_dir (str): job directory name
      animate_py (str): animate.py file
      fps (float, optional): [description]. Defaults to 10.
  """
  with open(animate_py, "w") as f:

    f.write("import cv2\n\n")
    f.write('animate_path = pathlib.Path("{0}" + "/animate")\n'.format(job_dir))
    f.write('movie = str(animate_path) + "/" + pathlib.Path(job_dir).name + ".mp4"\n')
    f.write("img = cv2.imread(pictures[0])\n")
    f.write('fourcc = cv2.VideoWriter_fourcc(*"mp4v")\n')
    f.write(
      "output = cv2.VideoWriter(movie, fourcc, {0}, (img.shape[1], img.shape[0]), True)\n".format(
        fps
      )
    )

    f.write('pictures = [str(p) for p in list(animate_path.glob("**/p_*.png"))]\n\n')
    f.write("for picture in pictures:\n")
    f.write("  img = cv2.imread(picture)\n")
    f.write("  output.write(img)\n")


def measure_height(ini_list: List[str], is_cluster: bool = False):
  """animate postprocess

  Args:
      ini_list (List[str]): list of ini files
      is_cluster (bool, optional): flag to apply for cluster job
  """
  for ini in ini_list:

    jobs, parameters, clusters, parallels = read_ini_file(ini)


def graph_height(ini_list: List[str], is_cluster: bool = False):
  """animate postprocess

  Args:
      ini_list (List[str]): list of ini files
      is_cluster (bool, optional): flag to apply for cluster job
  """
  for ini in ini_list:

    jobs, parameters, clusters, parallels = read_ini_file(ini)
