"""liggghts module containing support functions for simulations
"""
# import csv
# import inspect
# import numpy
import cv2
import math
import pathlib
import re
import shutil
import subprocess

# from matplotlib import pyplot
from typing import List, Tuple, Optional


def setup_simulation(ini_list: List[str], is_cluster: bool = False):
  """create liggghts simulation scripts

  Args:
      ini_list (List[str]): list of ini files
      is_cluster (bool): flag to apply for cluster job
  """
  for ini in ini_list:

    jobs, parameters, clusters, parallels = read_ini_file(ini)

    if not check_parameters(ini, jobs, parameters):
      continue
    if is_cluster and (not check_cluster_parameters(ini, jobs, clusters, parallels)):
      continue

    sim_path = pathlib.Path(pathlib.Path.cwd() / pathlib.Path(ini).stem)
    sim_path.mkdir(parents=True, exist_ok=True)
    home = str(pathlib.Path.home().resolve())
    sim_exe_sh = str(sim_path) + "/sim_exe.sh"
    qsub_sim_exe_sh = str(sim_path) + "/qsub_sim_exe.sh"

    with open(sim_exe_sh, "w") as f:
      f.write("#!/bin/bash\n\n")

    if is_cluster:
      with open(qsub_sim_exe_sh, "w") as f:
        f.write("#!/bin/bash\n\n")

    for idx, job in enumerate(jobs):

      job_dir = str(pathlib.Path(sim_path / job))
      if pathlib.Path(job_dir).is_dir():
        shutil.rmtree(job_dir)

      pathlib.Path(job_dir).mkdir(parents=True)
      np = parallels[idx]
      sim_sh = job_dir + "/sim.sh"
      ini_script = job_dir + "/ini.script"
      lmp = home + "/build/LIGGGHTS-PUBLIC/src/lmp_auto"

      with open(sim_exe_sh, "a") as f:
        f.write("cd {0}\n".format(job_dir))
        f.write("bash {0}\n".format(sim_sh))

      with open(sim_sh, "w") as f:
        f.write("#!/bin/bash\n\n")
        f.write("mpirun -np {0} {1} < {2}\n".format(np, lmp, ini_script))

      with open(ini_script, "w") as f:
        for parameter in parameters:
          f.write(parameter[0] + "\n" if len(parameter) == 1 else parameter[idx] + "\n")

      if not is_cluster:
        continue

      qsub_sim_sh = job_dir + "/qsub_sim.sh"
      hostfile = job_dir + "/hostfile"
      vtk = home + "/build/LIGGGHTS-PUBLIC/lib/vtk/install/lib"

      with open(qsub_sim_exe_sh, "a") as f:
        f.write("cd {0}\n".format(job_dir))
        f.write("qsub {0}\n".format(qsub_sim_sh))

      with open(hostfile, "w") as f:
        for host in clusters[idx].split("+"):
          f.write(host.strip() + "\n")

      with open(qsub_sim_sh, "w") as f:
        f.write("#!/bin/bash\n\n")
        f.write("#$ -cwd\n")
        f.write("#$ -N {0}\n".format(job))
        f.write("#$ -o stdout.liggghts\n")
        f.write("#$ -e stderr.liggghts\n")
        f.write("#$ -M Masato.Adachi@dlr.de\n")
        f.write("#$ -m es\n\n")

        f.write("/usr/mpi/gcc/openmpi-1.10.5a1/bin/mpirun")
        f.write(" -x LD_LIBRARY_PATH=$LD_LIBRARY_PATH:{0}".format(vtk))
        f.write(" -x HCOLL_ENABLE_MCAST_ALL=0")
        f.write(" -np {0}".format(str(np)))
        f.write(" --hostfile {0}".format(hostfile))
        f.write(" --mca opal_event_include poll")
        f.write(" --mca orte_base_help_aggregate 0")
        f.write(" --mca btl_openib_warn_default_gid_prefix to 0")
        f.write(' bash -c "ulimit -s 10240 && {0} < {1}"\n\n'.format(lmp, ini_script))


def execute_simulation(ini_list: List[str], is_cluster: bool = False):
  """execute liggghts simulation

  Args:
      ini_list (List[str]): list of ini files
      is_cluster (bool): flag to apply for cluster job
  """
  for ini in ini_list:

    sim_path = pathlib.Path(pathlib.Path.cwd() / pathlib.Path(ini).stem)
    sim_exe_sh = str(sim_path) + "/sim_exe.sh"
    qsub_sim_exe_sh = str(sim_path) + "/qsub_sim_exe.sh"
    subprocess.run(["bash", qsub_sim_exe_sh if is_cluster else sim_exe_sh])


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


def animate(ini_list: List[str], is_cluster: bool = False, fps: Optional[int] = None):
  """animate postprocess

  Args:
      ini_list (List[str]): list of ini files
      is_cluster (bool, optional): flag to apply for cluster job
      fps (Optional[int], optional): fps. If this is None, this becomes 10.
  """
  for ini in ini_list:

    fps_ffmpeg = fps if fps else 10
    jobs, parameters, clusters, parallels = read_ini_file(ini)
    sim_path = pathlib.Path(pathlib.Path.cwd() / pathlib.Path(ini).stem)
    animate_exe_sh = str(sim_path) + "/animate_exe.sh"
    qsub_animate_exe_sh = str(sim_path) + "/qsub_animate_exe.sh"

    with open(animate_exe_sh, "w") as f:
      f.write("#!/bin/bash\n\n")

    if is_cluster:
      with open(qsub_animate_exe_sh, "w") as f:
        f.write("#!/bin/bash\n\n")

    for idx, job in enumerate(jobs):

      np = parallels[idx]
      job_dir = str(pathlib.Path(sim_path / job))
      animate_dir = job_dir + "/animate"

      if pathlib.Path(animate_dir).is_dir():
        shutil.rmtree(animate_dir)
      pathlib.Path(animate_dir).mkdir(parents=True)

      write_animate_py(job_dir)
      animate_py = animate_dir + "/animate.py"
      animate_sh = animate_dir + "/animate.sh"
      log = animate_dir + "/log.animate"

      with open(animate_exe_sh, "a") as f:
        f.write("cd {0}\n".format(animate_dir))
        f.write("bash {0}\n".format(animate_sh))

      with open(animate_sh, "w") as f:
        f.write("#!/bin/bash\n\n")
        f.write(
          "mpirun -np {0} pvbatch --use-offscreen-rendering {1} 2>&1 | tee -a {2}\n".format(
            np, animate_py, log
          )
        )
        f.write(
          "ffmpeg -f image2 -y -framerate {0} -i {1}/p_.%04d.png -c:v libx264 -vf fps={0} -pix_fmt yuv420p {1}/{2}.mp4 2>&1 | tee -a {3}\n".format(
            fps_ffmpeg, animate_dir, job, log
          )
        )
        f.write("if [ -d {0} ]; then\nrm {0}/p_.*.png\nfi\n\n".format(animate_dir))

      if not is_cluster:
        continue

      qsub_animate_sh = animate_dir + "/qsub_animate.sh"
      pvbatch = str(pathlib.Path.home().resolve()) + "/build/paraview/bin/pvbatch"
      pvbatch_lib = str(pathlib.Path.home().resolve()) + "/build/paraview/lib"
      ffmpeg = "/usr/bin/ffmpeg"

      with open(qsub_animate_exe_sh, "a") as f:
        f.write("cd {0}\n".format(animate_dir))
        f.write("qsub {0}\n".format(qsub_animate_sh))

      with open(qsub_animate_sh, "w") as f:
        f.write("#!/bin/bash\n\n")
        f.write("#$ -cwd\n")
        f.write("#$ -N {0}\n".format(job))
        f.write("#$ -eo {0}\n".format(log))
        f.write("#$ -M Masato.Adachi@dlr.de\n")
        f.write("#$ -m ae\n\n")

        f.write("/usr/mpi/gcc/openmpi-1.10.5a1/bin/mpirun")
        f.write(" -x LD_LIBRARY_PATH=$LD_LIBRARY_PATH:{0}".format(pvbatch_lib))
        f.write(" -x HCOLL_ENABLE_MCAST_ALL=0")
        f.write(" -np {0}".format(str(np)))
        f.write(" --hostfile {0}".format(job_dir + "/hostfile"))
        f.write(" --mca opal_event_include poll")
        f.write(" --mca orte_base_help_aggregate 0")
        f.write(" --mca btl_openib_warn_default_gid_prefix to 0")
        f.write(
          ' bash -c "ulimit -s 10240 && {0} --use-offscreen-rendering {1}\n\n'.format(
            pvbatch, animate_py
          )
        )
        f.write(
          "{0} -framerate {1} -i {2}/p_.%04d.png -vcodec libx264 -pix_fmt yuv420p -y {2}/{3}.mp4\n".format(
            ffmpeg, fps_ffmpeg, animate_dir, job
          )
        )
        f.write("if [ -d {0} ]; then\nrm {0}/p_.*.png\nfi\n\n".format(animate_dir))

    subprocess.run(["bash", qsub_animate_exe_sh if is_cluster else animate_exe_sh])


def write_animate_py(job_dir: str):
  """write movie.py file

  Args:
      job_dir (str): job directory name
  """
  post_dir_path = pathlib.Path(job_dir + "/post")
  particles = [
    str(p) for p in list(post_dir_path.glob("**/p_*.vtk")) if "bounding" not in str(p)
  ]
  cads = [str(c) for c in post_dir_path.glob("**/cad_*.vtk")]
  boxes = [str(b) for b in post_dir_path.glob("**/*bounding*.vtk")]

  match = re.compile(r"\d+")
  particles.sort(key=lambda s: int(match.findall(s)[-1]))
  cads.sort(key=lambda s: int(match.findall(s)[-1]))
  boxes.sort(key=lambda s: int(match.findall(s)[-1]))

  with open(job_dir + "/animate/animate.py", "w") as f:
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
