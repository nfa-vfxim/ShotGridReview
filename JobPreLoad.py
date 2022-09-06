from System import *
from System.IO import *


def __main__(deadlinePlugin):
    job = deadlinePlugin.GetJob()
    deadlinePlugin.LogInfo("JobName: %s" % job.JobName)
    deadlinePlugin.LogInfo("JobId: %s" % job.JobId)

    # Any custom pre job code, such as adding environments
