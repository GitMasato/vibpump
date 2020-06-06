"""liggghts module containing support functions for simulations
"""
# import csv
# import inspect
# import numpy
import math
import pathlib
import shutil
import subprocess

# from matplotlib import pyplot
from typing import List, TextIO, Tuple


def read_conf_file(
  conf: str,
) -> Tuple[List[str], List[List[str]], List[str], List[int]]:
  """read conf file

  Args:
      conf (str): conf file

  Returns:
      Tuple[List[str], List[List[str]], List[str], List[int]]: jobs, parameters, cluster_parameters, numbers of parallel-processes
  """
  is_job, is_parameter, is_cluster = False, False, False
  jobs: List[str] = []
  parameter: List[str] = []
  parameters: List[List[str]] = []
  clusters: List[str] = []
  proc_size: List[int] = []

  with open(conf) as f:

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
        proc_size.append(1)
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
        for idx in range(len(proc_size)):
          proc_size[idx] = math.prod(
            [int(n) for n in parameter[0].split() if n.isnumeric()]
          )
    else:
      for idx, p in enumerate(parameter):
        if [n for n in p.split() if n.isnumeric()]:
          proc_size[idx] = math.prod([int(n) for n in p.split() if n.isnumeric()])

  return jobs, parameters, clusters, proc_size


def check_conf_input(conf: str, jobs: List[str], parameters: List[List[str]]) -> bool:
  """check if conf file inputs are correct

  Args:
      conf (str): conf file
      jobs (List[str]): jobs
      parameters (List[List[str]]): parameters

  Returns:
      bool: if inputs are correct (true:correct)
  """
  if not jobs:
    print("{0}: no job is given!".format(conf))
    return False

  if len(set(jobs)) != len(jobs):
    print("{0}: same job name exists!".format(conf))
    return False

  if " " in "".join(jobs):
    print("{0}: whitespace exists in job name!".format(conf))
    return False

  if not parameters:
    print("{0}: no parameter is given!".format(conf))
    return False

  unmatched = [p for p in parameters if not ((len(p) == len(jobs)) or (len(p) == 1))]
  if unmatched:
    print("{0}: parameter size is wrong!\n{1}\n".format(conf, unmatched))
    return False

  for parameter in parameters:

    if [p for p in parameter if "mesh/surface file " in p]:

      if len(parameter) == 1:

        splitted = parameter[0].split()
        cad_input_path = pathlib.Path(splitted[splitted.index("file") + 1])
        cad_file_path = pathlib.Path(conf).parent.resolve() / cad_input_path

        if not cad_file_path.is_file():
          print("{0}: cad file does not exist!\n{1}\n".format(conf, str(cad_file_path)))
          return False

        parameter[0] = parameter[0].replace(
          "file {0}".format(str(cad_input_path)),
          "file {0}".format(str(cad_file_path.resolve())),
        )

      else:

        for idx in range(len(parameter)):

          splitted = parameter[idx].split()
          cad_input_path = pathlib.Path(splitted[splitted.index("file") + 1])
          cad_file_path = pathlib.Path(conf).parent.resolve() / cad_input_path

          if not cad_file_path.is_file():
            print(
              "{0}: cad file does not exist!\n{1}\n".format(conf, str(cad_file_path))
            )
            return False

          parameter[idx] = parameter[idx].replace(
            "file {0}".format(str(cad_input_path)),
            "file {0}".format(str(cad_file_path.resolve())),
          )

    if [p for p in parameter if "read_restart " in p]:

      if len(parameter) == 1:

        splitted = parameter[0].split()
        restart_input = pathlib.Path(splitted[splitted.index("read_restart") + 1])
        restart_path = pathlib.Path(conf).parent.resolve() / restart_input

        if not restart_path.is_file():
          print("{0}: restart file does not exist!\n".format(conf))
          print("{0}\n".format(str(restart_path)))
          return False

        parameter[0] = parameter[0].replace(
          "read_restart {0}".format(str(restart_input)),
          "read_restart {0}".format(str(restart_path.resolve())),
        )

      else:

        for idx in range(len(parameter)):

          splitted = parameter[idx].split()
          restart_input = pathlib.Path(splitted[splitted.index("read_restart") + 1])
          restart_path = pathlib.Path(conf).parent.resolve() / restart_input

          if not restart_path.is_file():
            print("{0}: restart file does not exist!\n".format(conf))
            print("{0}\n".format(str(restart_path)))
            return False

          parameter[idx] = parameter[idx].replace(
            "read_restart {0}".format(str(restart_input)),
            "read_restart {0}".format(str(restart_path.resolve())),
          )

  return True


def check_cluster_input(
  conf: str, jobs: List[str], clusters: List[str], proc_sizes: List[int]
) -> bool:
  """check if conf file inputs are correct

  Args:
      conf (str): conf file
      jobs (List[str]): jobs
      clusters (List[str]): cluster parameters
      proc_sizes (List[int]): list of parallel process numbers

  Returns:
      bool: if inputs are correct (true:correct)
  """
  if not clusters:
    print("{0}: no cluster parameter is given!".format(conf))
    return False

  if len(clusters) != len(jobs):
    print("{0}: cluster parameter size is wrong!\n{1}\n".format(conf, clusters))
    return False

  c_proc_size = [1 for cluster in clusters]

  for idx, cluster in enumerate(clusters):
    c_proc_size[idx] = sum(
      [int(c.split("=")[1]) for c in cluster.split() if "slots=" in c]
    )

  if proc_sizes != c_proc_size:
    print("{0}: parallel process size is not equal!\n".format(conf))
    print("processors: {0}\nhostfile: {1}\n".format(proc_sizes, c_proc_size))
    return False

  return True


def check_post_existence(
  conf: str, jobs: List[str], clusters: List[str], proc_sizes: List[int]
) -> bool:
  """check if conf file inputs are correct

  Args:
      conf (str): conf file
      jobs (List[str]): jobs
      clusters (List[str]): cluster parameters
      proc_sizes (List[int]): list of parallel process numbers

  Returns:
      bool: if inputs are correct (true:correct)
  """
  if not clusters:
    print("{0}: no cluster parameter is given!".format(conf))
    return False

  if len(clusters) != len(jobs):
    print("{0}: cluster parameter size is wrong!\n{1}\n".format(conf, clusters))
    return False

  c_proc_size = [1 for cluster in clusters]

  for idx, cluster in enumerate(clusters):
    c_proc_size[idx] = sum(
      [int(c.split("=")[1]) for c in cluster.split() if "slots=" in c]
    )

  if proc_sizes != c_proc_size:
    print("{0}: parallel process size is not equal!\n".format(conf))
    print("processors: {0}\nhostfile: {1}\n".format(proc_sizes, c_proc_size))
    return False

  return True


def execute_sh(script: str) -> bool:
  """execute script

  Args:
      script (str): script file

  Returns:
      bool: if script is executed (true: executed)
  """
  if pathlib.Path(script).is_file():
    subprocess.run(["bash", script])
    return True
  else:
    print("'{0}' does not exists!".format(script))
    return False


def execute_qsub(script: str) -> bool:
  """execute script

  Args:
      script (str): script file

  Returns:
      bool: if script is executed (true: executed)
  """
  if pathlib.Path(script).is_file():
    subprocess.run(["qsub", script])
    return True
  else:
    print("'{0}' does not exists!".format(script))
    return False


def setup_sim(
  conf_list: List[str],
  is_cluster: bool = False,
  is_animated: bool = False,
  is_executed: bool = False,
):
  """create liggghts simulation scripts

  Args:
      conf_list (List[str]): list of conf files
      is_cluster (bool): flag to apply for cluster job
      is_animated (bool): flag to apply animate process
      is_executed (bool): flag to execute simulation
  """
  for conf in conf_list:

    jobs, parameters, clusters, proc_sizes = read_conf_file(conf)

    if not check_conf_input(conf, jobs, parameters):
      continue
    if is_cluster and (not check_cluster_input(conf, jobs, clusters, proc_sizes)):
      continue

    jobs_dir = str(pathlib.Path(conf).parent / pathlib.Path(conf).stem)
    pathlib.Path(jobs_dir).mkdir(parents=True, exist_ok=True)

    if is_cluster:
      with open(jobs_dir + "/qsub_sim_all.sh", "w") as f:
        write_ini_all_cluster(conf, jobs, proc_sizes, jobs_dir, f)
        write_sim_all_cluster(f)
        if is_animated:
          write_animate_all_cluster(f)
    else:
      with open(jobs_dir + "/sim_all.sh", "w") as f:
        write_ini_all(jobs, proc_sizes, jobs_dir, f)
        write_sim_all(f)
        if is_animated:
          write_animate_all(f)
        write_end_all(jobs, f)

    for idx, job in enumerate(jobs):

      job_dir = jobs_dir + "/" + job
      if pathlib.Path(job_dir).is_dir():
        shutil.rmtree(job_dir)
      pathlib.Path(job_dir).mkdir(parents=True)

      if is_animated:
        create_animate_dir(job_dir)

      with open(job_dir + "/in.script", "w") as f:
        for parameter in parameters:
          f.write(parameter[0] + "\n" if len(parameter) == 1 else parameter[idx] + "\n")

      if is_cluster:
        with open(job_dir + "/hostfile", "w") as f:
          for host in clusters[idx].split("+"):
            f.write(host.strip() + "\n")

        with open(job_dir + "/qsub_sim.sh", "w") as f:
          write_ini_cluster(job_dir, f)
          write_sim_cluster(job_dir, proc_sizes[idx], f)
          if is_animated:
            write_animate_cluster(job_dir, proc_sizes[idx], f)
      else:
        with open(job_dir + "/sim.sh", "w") as f:
          write_ini(f)
          write_sim(job_dir, proc_sizes[idx], f)
          if is_animated:
            write_animate(job_dir, proc_sizes[idx], f)

    if is_executed:
      if is_cluster:
        execute_qsub(jobs_dir + "/qsub_sim_all.sh")
      else:
        execute_sh(jobs_dir + "/sim_all.sh")


def setup_post(
  conf_list: List[str],
  is_cluster: bool = False,
  is_animated: bool = False,
  is_executed: bool = False,
):
  """post-process of liggghts simulation

  Args:
      conf_list (List[str]): list of conf files
      is_cluster (bool): flag to apply for cluster job
      is_animated (bool): flag to apply animate process
      is_executed (bool): flag to execute simulation
  """
  for conf in conf_list:

    jobs, parameters, clusters, proc_sizes = read_conf_file(conf)

    if not check_conf_input(conf, jobs, parameters):
      continue

    jobs_dir = str(pathlib.Path(conf).parent / pathlib.Path(conf).stem)
    pathlib.Path(jobs_dir).mkdir(parents=True, exist_ok=True)

    if is_cluster:
      with open(jobs_dir + "/qsub_post_all.sh", "w") as f:
        write_ini_all_cluster(conf, jobs, proc_sizes, jobs_dir, f)
        if is_animated:
          write_animate_all_cluster(f)
    else:
      with open(jobs_dir + "/post_all.sh", "w") as f:
        write_ini_all(jobs, proc_sizes, jobs_dir, f)
        if is_animated:
          write_animate_all(f)
        write_end_all(jobs, f)

    for idx, job in enumerate(jobs):

      job_dir = jobs_dir + "/" + job
      if is_animated:
        create_animate_dir(job_dir)

      if is_cluster:
        with open(job_dir + "/qsub_post.sh", "w") as f:
          write_ini_cluster(job_dir, f)
          if is_animated:
            write_animate_cluster(job_dir, proc_sizes[idx], f)
      else:
        with open(job_dir + "/post.sh", "w") as f:
          write_ini(f)
          if is_animated:
            write_animate(job_dir, proc_sizes[idx], f)

    if is_executed:
      if is_cluster:
        execute_qsub(jobs_dir + "/qsub_post_all.sh")
      else:
        execute_sh(jobs_dir + "/post_all.sh")


def write_ini_all(
  jobs: List[str], proc_sizes: List[int], jobs_dir: str, IO: TextIO,
):
  """write initial setting description

  Args:
      jobs (List[str]): jobs
      proc_sizes (List[int]): list of parallel process numbers
      jobs_dir (str): name of directory for jobs
      IO (io.TextIO): file object
  """
  list_str = "N_SIM_LIST=( " + " ".join([str(p) for p in proc_sizes]) + " )\n"
  list_str += "N_POST_LIST=( "
  list_str += " ".join([str(p) if p < 25 else "24" for p in proc_sizes]) + " )\n"
  list_str += "DIR_LIST=( "
  list_str += " ".join(['"{0}"'.format(jobs_dir + "/" + j) for j in jobs]) + " )\n\n"

  IO.write("#!/bin/bash\n\n")
  IO.write(list_str)
  IO.write("exe () {\n\n")
  IO.write("  cd ${1}\n\n")


def write_end_all(
  jobs: List[str], IO: TextIO,
):
  """write end description

  Args:
      jobs (List[str]): jobs
      IO (io.TextIO): file object
  """
  IO.write("}\n\n")
  IO.write("for D in $(seq {0}); do\n".format(len(jobs)))
  IO.write("  exe ${DIR_LIST[${D}-1]} \\\n")
  IO.write("  ${N_SIM_LIST[${D}-1]} ${N_POST_LIST[${D}-1]} &\n")
  IO.write("done\n\n")


def write_ini_all_cluster(
  conf: str, jobs: List[str], proc_sizes: List[int], jobs_dir: str, IO: TextIO,
):
  """write initial setting description

  Args:
      conf (str): conf file
      jobs (List[str]): jobs
      proc_sizes (List[int]): list of parallel process numbers
      jobs_dir (str): name of directory for jobs
      is_cluster (bool): flag to apply for cluster job
      IO (io.TextIO): file object
  """
  list_str = "N_SIM_LIST=( " + " ".join([str(p) for p in proc_sizes]) + " )\n"
  list_str += "N_POST_LIST=( "
  list_str += " ".join([str(p) if p < 25 else "24" for p in proc_sizes]) + " )\n"
  list_str += "DIR_LIST=( "
  list_str += " ".join(['"{0}"'.format(jobs_dir + "/" + j) for j in jobs]) + " )\n\n"

  IO.write("#!/bin/bash\n\n")
  IO.write("#$ -cwd\n")
  IO.write("#$ -t 1-{0}:1\n".format(str(len(jobs))))
  IO.write("#$ -o {0}\n".format(jobs_dir + "/out_sim"))
  IO.write("#$ -e {0}\n".format(jobs_dir + "/err_sim"))
  IO.write("#$ -N {0}\n\n".format(pathlib.Path(conf).name))
  IO.write(list_str)
  IO.write("N_SIM=${N_SIM_LIST[$SGE_TASK_ID-1]}\n")
  IO.write("N_POST=${N_POST_LIST[$SGE_TASK_ID-1]}\n")
  IO.write("DIR=${DIR_LIST[$SGE_TASK_ID-1]}\n\n")


def write_ini(IO: TextIO):
  """write initial setting description

  Args:
      IO (io.TextIO): file object
  """
  IO.write("#!/bin/bash\n\n")


def write_ini_cluster(job_dir: str, IO: TextIO):
  """write initial setting description

  Args:
      job_dir (str): job directory
      IO (io.TextIO): file object
  """
  IO.write("#!/bin/bash\n\n")
  IO.write("#$ -cwd\n")
  IO.write("#$ -o {0}\n".format(job_dir + "/out_post"))
  IO.write("#$ -e {0}\n".format(job_dir + "/err_post"))
  IO.write("#$ -N {0}\n\n".format(pathlib.Path(job_dir).name))


def write_sim_all(IO: TextIO):
  """write simulation process description

  Args:
      IO (io.TextIO): file object
  """
  lmp, vtk = get_lmp_vtk_path()
  IO.write("  mpirun \\\n")
  IO.write("  -x LD_LIBRARY_PATH=$LD_LIBRARY_PATH:{0} \\\n".format(vtk))
  IO.write("  -np ${2} \\\n")
  IO.write("  {0} < ".format(lmp) + "${1}/in.script >> ${1}/log.liggghts 2>&1\n\n")


def write_sim_all_cluster(IO: TextIO):
  """write simulation process description

  Args:
      IO (io.TextIO): file object
  """
  lmp, vtk = get_lmp_vtk_path()
  IO.write("/usr/mpi/gcc/openmpi-1.10.5a1/bin/mpirun")
  IO.write(" -x LD_LIBRARY_PATH=$LD_LIBRARY_PATH:{0}".format(vtk))
  IO.write(" -np ${N_SIM}")
  IO.write(" --hostfile ${DIR}/hostfile")
  IO.write(" --mca opal_event_include poll")
  IO.write(" --mca orte_base_help_aggregate 0")
  IO.write(" --mca btl_openib_warn_default_gid_prefix 0")
  IO.write(" bash -c")
  IO.write(' "ulimit -s 10240 && cd ${DIR} &&')
  IO.write(" {0} < ".format(lmp) + "${DIR}/in.script")
  IO.write(' >> ${DIR}/log.liggghts 2>&1"\n\n')


def write_sim(job_dir: str, proc_size: int, IO: TextIO):
  """write simulation process description

  Args:
      job_dir (str): job directory name
      proc_size (int): parallel process size
      IO (io.TextIO): file object
  """
  lmp, vtk = get_lmp_vtk_path()
  IO.write("cd {0}\n\n".format(job_dir))
  IO.write("mpirun \\\n")
  IO.write("-x LD_LIBRARY_PATH=$LD_LIBRARY_PATH:{0} \\\n".format(vtk))
  IO.write("-np {0} {1} < {2}\n\n".format(proc_size, lmp, job_dir + "/in.script"))


def write_sim_cluster(job_dir: str, proc_size: int, IO: TextIO):
  """write simulation process description

  Args:
      job_dir (str): job directory name
      proc_size (int): parallel process size
      IO (io.TextIO): file object
  """
  lmp, vtk = get_lmp_vtk_path()
  IO.write("/usr/mpi/gcc/openmpi-1.10.5a1/bin/mpirun")
  IO.write(" -x LD_LIBRARY_PATH=$LD_LIBRARY_PATH:{0}".format(vtk))
  IO.write(" -np {0}".format(proc_size))
  IO.write(" --hostfile {0}".format(job_dir + "/hostfile"))
  IO.write(" --mca opal_event_include poll")
  IO.write(" --mca orte_base_help_aggregate 0")
  IO.write(" --mca btl_openib_warn_default_gid_prefix 0")
  IO.write(" bash -c")
  IO.write(' "ulimit -s 10240 && cd {0} &&'.format(job_dir))
  IO.write(" {0} < {1}".format(lmp, job_dir + "/in.script"))
  IO.write(' >> {0} 2>&1"\n\n'.format(job_dir + "/log.liggghts"))


def get_lmp_vtk_path() -> Tuple[str, str]:

  home = str(pathlib.Path.home().resolve())
  lmp = home + "/build/LIGGGHTS-PUBLIC/src/lmp_auto"
  vtk = home + "/build/LIGGGHTS-PUBLIC/lib/vtk/install/lib"
  return lmp, vtk


def write_animate_all(IO: TextIO):
  """write simulation process description

  Args:
      is_cluster (bool): flag to apply for cluster job
      IO (io.TextIO): file object
  """
  mpiexec, pvbatch, python38 = get_mpiexec_pvbatch_python38_path()
  IO.write("  " + mpiexec + " -np ${3} \\\n")
  IO.write("  " + pvbatch + " --force-offscreen-rendering \\\n")
  IO.write("  ${1}/animate/pvbatch.py >> ${1}/log.post 2>&1\n\n")
  IO.write("  python3.8 ${1}/animate/animate.py >> ${1}/log.post 2>&1\n\n")


def write_animate_all_cluster(IO: TextIO):
  """write simulation process description

  Args:
      IO (io.TextIO): file object
  """
  mpiexec, pvbatch, python38 = get_mpiexec_pvbatch_python38_path()
  IO.write(mpiexec + " -np ${N_POST} \\\n")
  IO.write(pvbatch + " --force-offscreen-rendering \\\n")
  IO.write("${DIR}/animate/pvbatch.py >> ${DIR}/log.post 2>&1\n\n")
  IO.write("export LD_LIBRARY_PATH=$HOME/local/lib64:$LD_LIBRARY_PATH\n")
  IO.write(python38 + " ${DIR}/animate/animate.py >> ${DIR}/log.post 2>&1\n\n")


def write_animate(job_dir: str, proc_size: int, IO: TextIO):
  """write animate process description

  Args:
      job_dir (str): job directory name
      proc_size (int): parallel process size
      IO (io.TextIO): file object
  """
  mpiexec, pvbatch, python38 = get_mpiexec_pvbatch_python38_path()
  IO.write("{0} -np {1} {2} \\\n".format(mpiexec, proc_size, pvbatch))
  IO.write("--force-offscreen-rendering {0}/animate/pvbatch.py \\\n".format(job_dir))
  IO.write("| tee -a {0}/log.post\n\n".format(job_dir))
  IO.write("python3.8 {0}/animate/animate.py | tee -a {0}/log.post\n\n".format(job_dir))


def write_animate_cluster(job_dir: str, proc_size: int, IO: TextIO):
  """write animate process description

  Args:
      job_dir (str): job directory name
      proc_size (int): parallel process size
      IO (io.TextIO): file object
  """
  mpiexec, pvbatch, python38 = get_mpiexec_pvbatch_python38_path()
  IO.write("{0} -np {1} {2} \\\n".format(mpiexec, proc_size, pvbatch))
  IO.write("--force-offscreen-rendering {0}/animate/pvbatch.py \\\n".format(job_dir))
  IO.write(">> {0}/log.post 2>&1\n\n".format(job_dir))
  IO.write("export LD_LIBRARY_PATH=$HOME/local/lib64:$LD_LIBRARY_PATH\n")
  IO.write("{0} {1}/animate/animate.py \\\n".format(python38, job_dir))
  IO.write(">> {0}/log.post 2>&1\n\n".format(job_dir))


def get_mpiexec_pvbatch_python38_path() -> Tuple[str, str, str]:

  home = str(pathlib.Path.home().resolve())
  mpiexec = home + "/build/paraview/paraview/bin/mpiexec"
  pvbatch = home + "/build/paraview/paraview/bin/pvbatch"
  python38 = home + "/local/bin/python3.8"
  return mpiexec, pvbatch, python38


def create_animate_dir(job_dir: str):
  """create directory and python script for animate process

  Args:
      job_dir (str): job directory name
  """
  if pathlib.Path(job_dir + "/animate").is_dir():
    shutil.rmtree(job_dir + "/animate")

  pathlib.Path(job_dir + "/animate").mkdir(parents=True)
  create_pvbatch_py(job_dir)
  create_animate_py(job_dir)


def create_pvbatch_py(job_dir: str):
  """write pvbatch.py file

  Args:
      job_dir (str): job directory name
  """
  with open(job_dir + "/animate/pvbatch.py", "w") as f:

    f.write("import glob\n")
    f.write("import re\n")
    f.write("from paraview.simple import *\n\n")

    f.write("paraview.simple._DisableFirstRenderCameraReset()\n")
    f.write('animate_dir = "{0}"\n'.format(job_dir + "/animate"))
    f.write('post_dir = "{0}"\n\n'.format(job_dir + "/post"))

    f.write(
      "ptcls = [p for p in glob.glob(post_dir + '/p_*.vtk') if 'bounding' not in p]\n"
    )
    f.write("boxes = glob.glob(post_dir + '/*bounding*.vtk')\n")
    f.write("cads = glob.glob(post_dir + '/cad_*.vtk')\n\n")

    f.write('match = re.compile(r"\d+")\n')
    f.write("ptcls.sort(key=lambda s: int(match.findall(s)[-1]))\n")
    f.write("boxes.sort(key=lambda s: int(match.findall(s)[-1]))\n")
    f.write("p_ = LegacyVTKReader(FileNames=ptcls)\n")
    f.write("p_boundingBox_ = LegacyVTKReader(FileNames=boxes)\n")
    f.write("if cads:\n")
    f.write("  cads.sort(key=lambda s: int(match.findall(s)[-1]))\n")
    f.write("  cad_ = LegacyVTKReader(FileNames=cads)\n\n")

    f.write("animationScene1 = GetAnimationScene()\n")
    f.write("animationScene1.UpdateAnimationUsingDataTimeSteps()\n")
    f.write('renderView1 = GetActiveViewOrCreate("RenderView")\n\n')

    f.write("p_Display = Show(p_, renderView1)\n")
    f.write('p_Display.Representation = "Surface"\n')
    f.write("p_boundingBox_Display = Show(p_boundingBox_, renderView1)\n")
    f.write('p_boundingBox_Display.Representation = "Outline"\n')
    f.write("if cads:\n")
    f.write("  cad_Display = Show(cad_, renderView1)\n")
    f.write('  cad_Display.Representation = "Surface"\n\n')

    f.write('glyph1 = Glyph(Input=p_, GlyphType="Sphere")\n')
    f.write('glyph1.ScaleArray = ["POINTS", "radius"]\n')
    f.write("glyph1.ScaleFactor = 2.0\n")
    f.write('glyph1.GlyphMode = "All Points"\n')
    f.write("glyph1Display = Show(glyph1, renderView1)\n")
    f.write('glyph1Display.Representation = "Surface"\n')
    f.write('ColorBy(glyph1Display, ("POINTS", "f", "Magnitude"))\n')
    f.write("Hide(p_, renderView1)\n\n")

    f.write("clip1 = Clip(Input=glyph1)\n")
    f.write('clip1.ClipType = "Plane"\n')
    f.write("clip1.ClipType.Origin = [0.0, 0.0, 0.0]\n")
    f.write("clip1.ClipType.Normal = [0.0, 1.0, 0.0]\n")
    f.write("clip1Display = Show(clip1, renderView1)\n")
    f.write('clip1Display.Representation = "Surface"\n')
    f.write("Hide(glyph1, renderView1)\n\n")

    f.write("if cads:\n")
    f.write("  clip2 = Clip(Input=cad_)\n")
    f.write('  clip2.ClipType = "Plane"\n')
    f.write("  clip2.ClipType.Origin = [0.0, 0.0, 0.0]\n")
    f.write("  clip2.ClipType.Normal = [0.0, 1.0, 0.0]\n")
    f.write("  clip2Display = Show(clip2, renderView1)\n")
    f.write('  clip2Display.Representation = "Surface"\n')
    f.write("  Hide(cad_, renderView1)\n\n")

    f.write("annotateTimeFilter1 = AnnotateTimeFilter(Input=clip1)\n")
    f.write('annotateTimeFilter1.Format = "Step: %.0f"\n')
    f.write("annotateTimeFilter1Display = Show(annotateTimeFilter1, renderView1)\n\n")

    f.write("renderView1.Update()\n")
    f.write("SetActiveSource(None)\n")
    f.write("renderView1.CameraPosition = [0.0, 0.5, 0.09]\n")
    f.write("renderView1.CameraFocalPoint = [0.0, 0.0, 0.09]\n")
    f.write("renderView1.CameraViewUp = [0.0, 0.0, 1.0]\n")
    f.write("renderView1.CameraParallelScale = 0.12\n\n")

    f.write("SaveAnimation(\n")
    f.write('  animate_dir + "/p_.png",\n')
    f.write("  renderView1,\n")
    f.write("  ImageResolution=[480, 640],\n")
    f.write("  FrameWindow=[0, len(ptcls)],\n")
    f.write("  SuffixFormat='.%05d'\n")
    f.write(")\n\n")


def create_animate_py(job_dir: str, fps: float = 10):
  """write animate.py file

  Args:
      job_dir (str): job directory name
      fps (float, optional): fps. Defaults to 10.
  """
  with open(job_dir + "/animate/animate.py", "w") as f:

    f.write("import cv2\n")
    f.write("import pathlib\n\n")

    f.write('job_dir = "{0}"\n'.format(job_dir))
    f.write('animate_path = pathlib.Path(job_dir + "/animate")\n')
    f.write('pictures = [str(p) for p in list(animate_path.glob("**/p_*.png"))]\n\n')

    f.write('movie = str(animate_path) + "/" + pathlib.Path(job_dir).name + ".mp4"\n')
    f.write("img = cv2.imread(pictures[0])\n")
    f.write("fps = {0}\n".format(fps if fps else 10))
    f.write('fourcc = cv2.VideoWriter_fourcc(*"mp4v")\n')
    f.write("output = cv2.VideoWriter")
    f.write("(movie, fourcc, fps, (img.shape[1], img.shape[0]), True)\n\n")

    f.write("for picture in pictures:\n")
    f.write("  img = cv2.imread(picture)\n")
    f.write("  output.write(img)\n\n")

    f.write("for picture in pictures:\n")
    f.write("  if pathlib.Path(picture).is_file():\n")
    f.write("    pathlib.Path(picture).unlink()\n\n")


def measure_height(conf_list: List[str], is_cluster: bool = False):
  """animate postprocess

  Args:
      conf_list (List[str]): list of conf files
      is_cluster (bool, optional): flag to apply for cluster job
  """
  for conf in conf_list:

    jobs, parameters, clusters, proc_size = read_conf_file(conf)


def graph_height(conf_list: List[str], is_cluster: bool = False):
  """animate postprocess

  Args:
      conf_list (List[str]): list of conf files
      is_cluster (bool, optional): flag to apply for cluster job
  """
  for conf in conf_list:

    jobs, parameters, clusters, proc_size = read_conf_file(conf)


def execute_sim(conf_list: List[str], is_cluster: bool = False):
  """execute simulation

  Args:
      conf_list (List[str]): list of conf files
      is_cluster (bool): flag to apply for cluster job
  """
  for conf in conf_list:

    jobs_dir = str(pathlib.Path(conf).parent / pathlib.Path(conf).stem)

    if is_cluster:
      execute_qsub(jobs_dir + "/qsub_sim_all.sh")
    else:
      execute_sh(jobs_dir + "/sim_all.sh")


def execute_post(conf_list: List[str], is_cluster: bool = False):
  """execute post process

  Args:
      conf_list (List[str]): list of conf files
      is_cluster (bool): flag to apply for cluster job
  """
  for conf in conf_list:

    jobs_dir = str(pathlib.Path(conf).parent / pathlib.Path(conf).stem)

    if is_cluster:
      execute_qsub(jobs_dir + "/qsub_post_all.sh")
    else:
      execute_sh(jobs_dir + "/post_all.sh")


def copy_result(
  conf_list: List[str],
  is_movie: bool = False,
  is_log_sim: bool = False,
  is_log_post: bool = False,
):
  """display log file

  Args:
      conf_list (List[str]): list of conf files
      is_movie (bool, optional): flag to copy simulation movie. Defaults to False.
      is_log_sim (bool, optional): flag to copy simulation log. Defaults to False.
      is_log_post (bool, optional): flag to copy post-process log. Defaults to False.
  """
  for conf in conf_list:

    home = str(pathlib.Path.home().resolve())
    gsync_dir = home + "/share/gsync"
    cp_dir = gsync_dir

    jobs, parameters, clusters, parallels = read_conf_file(conf)
    jobs_dir = str(pathlib.Path(conf).parent / pathlib.Path(conf).stem)

    for job in jobs:

      cp_job_dir = cp_dir + "/" + job
      pathlib.Path(cp_job_dir).mkdir(parents=True, exist_ok=True)

      movie = jobs_dir + "/" + job + "/animate/" + job + ".mp4"
      log_liggghts = jobs_dir + "/" + job + "/log.liggghts"
      log_post = jobs_dir + "/" + job + "/log.post"

      if is_movie:
        if pathlib.Path(movie).is_file():
          subprocess.run(["cp", movie, cp_job_dir])
          print("'{0}' is copied to '{1}'!".format(movie, cp_job_dir))
        else:
          print("'{0}' does not exists!".format(movie))

      if is_log_sim:
        if pathlib.Path(log_liggghts).is_file():
          subprocess.run(["cp", log_liggghts, cp_job_dir])
          print("'{0}' is copied to '{1}'!".format(log_liggghts, cp_job_dir))
        else:
          print("'{0}' does not exists!".format(log_liggghts))

      if is_log_post:
        if pathlib.Path(log_post).is_file():
          subprocess.run(["cp", log_post, cp_job_dir])
          print("'{0}' is copied to '{1}'!".format(log_post, cp_job_dir))
        else:
          print("'{0}' does not exists!".format(log_post))


def display_log(
  conf_list: List[str], log_type: str = None, is_head: bool = False, lines: int = 15,
):
  """display log file

  Args:
      conf_list (List[str]): list of conf files
      log_type (str, optional): type log to be displayed.
      is_head (bool, optional): flag to show head part of log file. Defaults to False.
      lines (int, optional): how many lines will be shown. Defaults to 25.
  """
  if not log_type:
    print("no log 'type' is specified!")
    return False

  for conf in conf_list:

    jobs, parameters, clusters, proc_size = read_conf_file(conf)
    jobs_dir = str(pathlib.Path(conf).parent / pathlib.Path(conf).stem)
    str_lines = str(lines) if lines else "25"

    for job in jobs:

      if log_type == "log-sim":
        log = jobs_dir + "/" + job + "/log.liggghts"
      elif log_type == "log-post":
        log = jobs_dir + "/" + job + "/log.post"
      elif log_type == "log-sim-all":
        pass
      elif log_type == "log-post-all":
        pass

      if pathlib.Path(log).is_file():
        print("\n///// {0} /////\n".format(log))
        subprocess.run(["head" if is_head else "tail", log, "-n", str_lines])
      else:
        print("'{0}' does not exists!".format(log))
