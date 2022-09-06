from Deadline.Plugins import *
from Deadline.Scripting import *
import os


def GetDeadlinePlugin():
    return ShotGridReviewPlugin()


def CleanupDeadlinePlugin(deadlinePlugin):
    deadlinePlugin.Cleanup()


class ShotGridReviewPlugin(DeadlinePlugin):
    def __init__(self):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument

    def Cleanup(self):
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback

    def InitializeProcess(self):
        self.PluginType = PluginType.Simple

    def RenderExecutable(self):
        exe = ""
        exeList = self.GetConfigEntry("Nuke_RenderExecutable")
        exe = FileUtils.SearchFileList(exeList)
        if exe == "":
            self.FailRender(
                "Nuke render executable was not found "
                "in the configured separated list %s" % str(exeList)
            )
        return exe

    def RenderArgument(self):
        plugin_path = os.path.dirname(os.path.realpath(__file__))
        deadline_review = os.path.join(
            plugin_path, "deadline_shotgrid_review_cli.py"
        ).replace(os.sep, "/")

        publish_id = self.GetPluginInfoEntryWithDefault("PublishID", "")
        first_frame = self.GetPluginInfoEntryWithDefault("FirstFrame", "")
        last_frame = self.GetPluginInfoEntryWithDefault("LastFrame", "")
        sequence_path = self.GetPluginInfoEntryWithDefault(
            "SequencePath", self.GetDataFilename()
        )
        sequence_path = sequence_path.replace(os.sep, "/")

        slate_path = self.GetPluginInfoEntryWithDefault(
            "SlatePath", self.GetDataFilename()
        )
        slate_path = slate_path.replace(os.sep, "/")

        fps = self.GetPluginInfoEntryWithDefault("FPS", "")

        company = self.GetPluginInfoEntryWithDefault("Company", "")

        colorspace_idt = self.GetPluginInfoEntryWithDefault(
            "ColorspaceIDT", ""
        )
        colorspace_odt = self.GetPluginInfoEntryWithDefault(
            "ColorspaceODT", ""
        )

        arguments = [
            "-t",
            deadline_review,
            first_frame,
            last_frame,
            fps,
            publish_id,
            sequence_path,
            slate_path,
            '"%s"' % company,
            '"%s"' % colorspace_idt,
            '"%s"' % colorspace_odt,
        ]

        argument = " ".join(map(str, arguments))

        return argument
