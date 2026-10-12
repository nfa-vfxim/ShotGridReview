from System import *
from System.IO import *


def __main__(deadlinePlugin):
    job = deadlinePlugin.GetJob()
    deadlinePlugin.LogInfo("JobName: %s" % job.JobName)
    deadlinePlugin.LogInfo("JobId: %s" % job.JobId)

    deadlinePlugin.LogInfo("Setting PYTHONPATH variable")
    python_path = "C:/pipeline/packages"
    deadlinePlugin.SetProcessEnvironmentVariable("PYTHONPATH", python_path)

    # Nuke -t only uses the OCIO variable for its config, so make sure the
    # pipeline config is used on Workers that don't have it set.
    if not Environment.GetEnvironmentVariable("OCIO"):
        ocio_config = "C:/pipeline/common/ocio/config/config.ocio"
        deadlinePlugin.LogInfo("Setting OCIO variable to %s" % ocio_config)
        deadlinePlugin.SetProcessEnvironmentVariable("OCIO", ocio_config)
