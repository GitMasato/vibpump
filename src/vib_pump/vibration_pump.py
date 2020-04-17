from vibration_pump_process import VibrationPumpProcess

if __name__ == "__main__":

  vib_proc = VibrationPumpProcess()

  vib_proc.CheckCommandLineArguments()
  vib_proc.CheckExistenceOfMovieFiles()

  vib_proc.CaptureMovies()
  vib_proc.RotatePictures()
  vib_proc.CropPictures()
  vib_proc.BinarizePictures()
  vib_proc.MeasurePictures()

  vib_proc.ShowAnalyzedData()
  vib_proc.CleanAnalyzedData()
