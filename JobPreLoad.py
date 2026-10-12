from System import *
from System.IO import *


def __main__(deadlinePlugin):
    job = deadlinePlugin.GetJob()
    deadlinePlugin.LogInfo("JobName: %s" % job.JobName)
    deadlinePlugin.LogInfo("JobId: %s" % job.JobId)

    deadlinePlugin.LogInfo("Setting PYTHONPATH variable")
    python_path = "C:/pipeline/packages"
    deadlinePlugin.SetProcessEnvironmentVariable("PYTHONPATH", python_path)
