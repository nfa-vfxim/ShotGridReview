"""ShotGrid Review
Netherlands Filmacademy 2022

Will use Nuke to automatically create a slate
with Netherlands Filmacademy design, transcode it
and upload to ShotGrid
"""

import nuke
import shotgun_api3
import os
import re
from datetime import datetime


class ShotGridReview(object):
    """Creates slate provided by publish data, transcodes and
    uploads to ShotGrid.

    Args:
            publish_id (int): associated publish id
            first_frame (int): first frame from frame sequence
            last_frame (int): first frame from frame sequence
            sequence_path (str): path to frame sequence
            slate_path (str): path to render slate
            shotgrid_site (str): url for ShotGrid site
            script_name (str): API name for script on ShotGrid
            script_key (str): API key for script on ShotGrid
            fps (float, optional): fps used by project. Defaults to 25.0.
            company (str, optional): company name to add to slate. Defaults to "ShotGrid".
            colorspace_idt (str, optional): _description_.
            Defaults to "ACES - ACEScg".
            colorspace_odt (str, optional): _description_.
            Defaults to "Output - sRGB".
    """

    def __init__(
        self,
        publish_id,
        first_frame,
        last_frame,
        sequence_path,
        slate_path,
        shotgrid_site,
        script_name,
        script_key,
        fps=25.0,
        company="ShotGrid",
        colorspace_idt="ACES - ACEScg",
        colorspace_odt="Output - sRGB",
    ):

        # Get script directory to add gizmo
        script_directory = os.path.dirname(os.path.realpath(__file__))
        gizmo_directory = os.path.join(script_directory, "gizmo")
        gizmo_directory = gizmo_directory.replace(os.sep, "/")
        # gizmo_directory = "//nfa-vfxim-deadline.ahk.nl/deadline/custom/plugins/ShotGridReview/gizmo"

        nuke.pluginAddPath(gizmo_directory)

        # Setting connection to ShotGrid with API
        self.sg = shotgun_api3.Shotgun(
            shotgrid_site, script_name=script_name, api_key=script_key
        )

        # Get frame sequences by path
        sequence = self.__validate_sequence(sequence_path)

        # If sequence is found, proceed
        if sequence:
            read = self.__setup_script(
                sequence_path=sequence_path,
                first_frame=first_frame,
                last_frame=last_frame,
                fps=fps,
                sequence=sequence,
                colorspace_idt=colorspace_idt,
            )

            # Get publish data
            publish_data = self.__get_publish_data(publish_id)

            # Create slate
            slate = self.__setup_slate(
                read_node=read,
                publish_data=publish_data,
                company=company,
                first_frame=first_frame,
                last_frame=last_frame,
                fps=fps,
                colorspace_idt=colorspace_idt,
                colorspace_odt=colorspace_odt,
            )

            # Create write node
            write = self.__setup_write(
                slate_node=slate,
                slate_path=slate_path,
                colorspace_odt=colorspace_odt,
                fps=fps,
            )

            # Render slate
            self.__render_slate(
                write_node=write,
                first_frame=first_frame,
                last_frame=last_frame,
            )

            # Upload slate to ShotGrid
            self.__upload_to_shotgrid(
                publish_data=publish_data,
                slate_path=slate_path,
                sequence_path=sequence_path,
                first_frame=first_frame,
                last_frame=last_frame,
                fps=fps,
                colorspace_odt=colorspace_odt,
            )

    def __validate_sequence(
        self,
        sequence_path,
    ):
        """Check if sequence is existing

        Args:
            sequence_path (str): sequence to check

        Returns:
            str or False: if validated returns sequence containing frame list
        """
        sequence_directory = os.path.dirname(sequence_path)
        sequence_filename = os.path.basename(sequence_path)

        sequences = self.__get_frame_sequences(sequence_directory)

        for sequence in sequences:
            filename = os.path.basename(sequence[0])

            if "1001" in filename:
                print("Found incorrectly filename, fixing frame padding")
                filename = filename.replace("1001", "%04d")

            if sequence_filename == filename:
                return sequence

        raise Exception("No frame sequence found")

    @staticmethod
    def __setup_script(
        sequence_path,
        first_frame,
        last_frame,
        fps,
        sequence,
        colorspace_idt,
    ):
        """Creates Nuke script with read node and correct settings

        Args:
            sequence_path (str): path to file sequence
            first_frame (str): first frame for sequence
            last_frame (str): last frame for sequence
            fps (str): fps used for project
            sequence (list): list containing both sequence path and frame list
            colorspace_idt (str): colorspace used by read node

        Returns:
            attribute: created read node
        """
        # Setup Nuke script
        nuke.root().knob("first_frame").setValue(first_frame)
        nuke.root().knob("last_frame").setValue(last_frame)
        nuke.root().knob("fps").setValue(fps)
        nuke.root().knob("colorManagement").setValue("OCIO")
        nuke.root().knob("OCIO_config").setValue(1)

        print("Setup script completed")

        # Setup read node
        read = nuke.createNode("Read")
        read.knob("file").setValue(sequence_path)

        first_sequence_frame = int(min(sequence[1]))
        last_sequence_frame = int(max(sequence[1]))

        # Set found frame range by sequence find function
        read.knob("first").setValue(first_sequence_frame)
        read.knob("origfirst").setValue(first_sequence_frame)
        read.knob("last").setValue(last_sequence_frame)
        read.knob("origlast").setValue(last_sequence_frame)

        read.knob("colorspace").setValue(colorspace_idt)
        read.knob("on_error").setValue("checkerboard")

        print("Created read node")

        # Return created read node
        return read

    def __get_publish_data(
        self,
        publish_id,
    ):
        """Search ShotGrid database for associated publish data

        Args:
            publish_id (int): id of publish

        Returns:
            dict: containing all publish data

            E.g.:
            {
                "type": "PublishedFile",
                "id": 42421,
                "created_by": {
                    "id": 1,
                    "name": "Example User",
                    "type": "HumanUser",
                },
                "code": "iwr_pri_pri_0030_scene_main_v014.%04d.exr",
                "task": {"id": 24136, "name": "comp", "type": "Task"},
                "project": {"id": 2602, "name": "it_will_rain",
                            "type": "Project"},
                "entity": {"id": 7193, "name": "pri_0030", "type": "Shot"},
                "description": "Integrated DMP",
                "version_number": 14,
            }
        """
        # Create the filter to search on ShotGrid
        # for publishes with the same file name
        filters = [
            ["id", "is", publish_id],
        ]

        columns = [
            "created_by",
            "code",
            "task",
            "project",
            "entity",
            "description",
            "version_number",
        ]

        # Search on ShotGrid
        publish = self.sg.find_one("PublishedFile", filters, columns)

        print("Got publish data")

        return publish

    @staticmethod
    def __setup_slate(
        read_node,
        publish_data,
        company,
        first_frame,
        last_frame,
        fps,
        colorspace_idt,
        colorspace_odt,
    ):
        """Setup slate with correct parameters

        Args:
            read_node (attribute): read node to connect slate to
            publish_data (dict): dictionary containing publish data
            company (str): name used for company knob
            first_frame (int): first frame by frame sequence
            last_frame (int): last frame by frame sequence
            fps (float): fps used by sequence
            colorspace_idt (str): colorspace for idt
            colorspace_odt (str): colorspace for odt

        Returns:
            attribute: created slate node
        """

        # Create slate node
        slate = nuke.createNode("nfaSlate")

        # Get project name
        project_name = publish_data.get("project")
        project_name = project_name.get("name")

        slate.knob("project").setValue(project_name)

        # Set company name
        slate.knob("company").setValue(company)

        # Get file name from publish data
        submission_name = publish_data.get("code")
        slate.knob("file").setValue(submission_name)

        # Create frame list
        frame_list = "%s - %s (%s)" % (
            first_frame,
            last_frame,
            str(int(last_frame) - int(first_frame)),
        )
        slate.knob("frameList").setValue(frame_list)

        # Get current time
        date = datetime.now()
        date = date.strftime("%d/%m/%Y %H:%M")
        slate.knob("date").setValue(date)

        # Get artist name
        artist = publish_data.get("created_by")
        artist = artist.get("name")

        slate.knob("artist").setValue(artist)

        task = publish_data.get("task")
        task = task.get("name")

        slate.knob("task").setValue(task)

        # Get version number
        version = publish_data.get("version_number")
        version = "v%03d" % version

        slate.knob("version").setValue(version)

        # Set FPS
        slate.knob("fps").setValue(fps)

        # Set colorspace
        slate.knob("colorspaceIDT").setValue(colorspace_idt)
        slate.knob("colorspaceODT").setValue(colorspace_odt)

        # Get description
        description = publish_data.get("description")
        slate.knob("description").setValue(description)

        # Set read node as input for slate node
        slate.setInput(0, read_node)

        # Return created node
        return slate

    @staticmethod
    def __setup_write(
        slate_node,
        slate_path,
        colorspace_odt,
        fps,
    ):
        """Create write node with correct settings

        Args:
            slate_node (attribute): node to connect write node to
            slate_path (str): path to render slate to
            colorspace_odt (str): output device transform used to render slate
            fps (float): fps used for rendering slate

        Returns:
            attribute: created write node
        """

        # Create write node
        write = nuke.createNode("Write")
        # Set write node settings
        write.knob("file").setValue(slate_path)
        write.knob("colorspace").setValue(colorspace_odt)

        # Set input
        write.setInput(0, slate_node)

        # Create directories
        slate_directory = os.path.dirname(slate_path)
        if not os.path.isdir(slate_directory):
            print("Slate directory doesn't exist, creating one")
            os.makedirs(slate_directory)

        return write

    @staticmethod
    def __render_slate(
        write_node,
        first_frame,
        last_frame,
    ):
        """Render specified write node

        Args:
            write_node (attribute): write node to render
            first_frame (int): first frame from sequence, will add one in front
            for slate
            last_frame (int): last frame from sequence
        """

        try:
            nuke.execute(write_node, first_frame - 1, last_frame)
            print("Rendering complete")

        except Exception as error:
            print("Could not render because %s" % str(error))

    def __upload_to_shotgrid(
        self,
        publish_data,
        slate_path,
        sequence_path,
        first_frame,
        last_frame,
        fps,
        colorspace_odt,
    ):
        """When slate has been created, upload to ShotGrid
        writh provided data and publish data.

        Args:
            publish_data (dict): dictionary containing all associated
            publish data
            slate_path (str): path to rendered slate
            first_frame (int): first frame from sequence
            last_frame (int): last frame from sequence
            fps (float): project fps
            colorspace_odt (str): colorspace slate is rendered in
        """
        project = publish_data.get("project")

        submission_name = publish_data.get("code")

        description = publish_data.get("description")

        entity = publish_data.get("entity")

        task = publish_data.get("task")
        task_id = task.get("id")

        user = publish_data.get("created_by")

        publish_id = publish_data.get("id")

        data = {
            "project": project,
            "code": submission_name,
            "description": description,
            "sg_colorspace": colorspace_odt,
            "sg_path_to_movie": slate_path,
            "sg_path_to_frames": sequence_path,
            "sg_status_list": "rev",
            "sg_first_frame": first_frame,
            "sg_last_frame": last_frame,
            "sg_uploaded_movie_frame_rate": fps,
            "frame_range": "%s-%s" % (first_frame, last_frame),
            "sg_movie_has_slate": True,
            "entity": entity,
            "sg_task": task,
            "user": user,
            "published_files": [{"type": "PublishedFile", "id": publish_id}],
        }

        # Create Version
        version = self.sg.create("Version", data).get("id")

        # Upload to ShotGrid
        self.sg.upload("Version", version, slate_path, "sg_uploaded_movie")

        print("Uploaded to ShotGrid")

        # Update task status to review
        self.sg.update("Task", task_id, {"sg_status_list": "rev"})

    @staticmethod
    def __get_frame_sequences(
        folder,
        extensions=None,
        frame_spec=None,
    ):
        """
        Copied from the publisher plugin, and customized to return file
        sequences with frame lists instead of filenames
        Given a folder, inspect the contained files to find what appear to be
        files with frame numbers.
        :param folder: The path to a folder potentially containing a
        sequence of
            files.
        :param extensions: A list of file extensions to retrieve paths for.
            If not supplied, the extension will be ignored.
        :param frame_spec: A string to use to represent the frame number in the
            return sequence path.
        :return: A list of tuples for each identified frame sequence. The first
            item in the tuple is a sequence path with the frame number replaced
            with the supplied frame specification. If no frame spec is
            supplied,
            a python string format spec will be returned with the padding found
            in the file.
            Example::
            get_frame_sequences(
                "/path/to/the/folder",
                ["exr", "jpg"],
                frame_spec="{FRAME}"
            )
            [
                (
                    "/path/to/the/supplied/folder/key_light1.{FRAME}.exr",
                    [<frame_1_framenumber>, <frame_2_framenumber>, ...]
                ),
                (
                    "/path/to/the/supplied/folder/fill_light1.{FRAME}.jpg",
                    [<frame_1_framenumber>, <frame_2_framenumber>, ...]
                )
            ]
        """
        FRAME_REGEX = re.compile(r"(.*)([._-])(\d+)\.([^.]+)$", re.IGNORECASE)

        # list of already processed file names
        processed_names = {}

        # examine the files in the folder
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)

            if os.path.isdir(file_path):
                # ignore subfolders
                continue

            # see if there is a frame number
            frame_pattern_match = re.search(FRAME_REGEX, filename)

            if not frame_pattern_match:
                # no frame number detected. carry on.
                continue

            prefix = frame_pattern_match.group(1)
            frame_sep = frame_pattern_match.group(2)
            frame_str = frame_pattern_match.group(3)
            extension = frame_pattern_match.group(4) or ""

            # filename without a frame number.
            file_no_frame = "%s.%s" % (prefix, extension)

            if file_no_frame in processed_names:
                # already processed this sequence. add the framenumber to the
                # list, later we can use this to determine the framerange
                processed_names[file_no_frame]["frame_list"].append(frame_str)
                continue

            if extensions and extension not in extensions:
                # not one of the extensions supplied
                continue

            # make sure we maintain the same padding
            if not frame_spec:
                padding = len(frame_str)
                frame_spec = "%%0%dd" % (padding,)

            seq_filename = "%s%s%s" % (prefix, frame_sep, frame_spec)

            if extension:
                seq_filename = "%s.%s" % (seq_filename, extension)

            # build the path in the same folder
            seq_path = os.path.join(folder, seq_filename)

            # remember each seq path identified and a
            # list of files matching the
            # seq pattern
            processed_names[file_no_frame] = {
                "sequence_path": seq_path,
                "frame_list": [frame_str],
            }

        # build the final list of sequence paths to return
        frame_sequences = []
        for file_no_frame in processed_names:
            seq_info = processed_names[file_no_frame]
            seq_path = seq_info["sequence_path"]

            frame_sequences.append((seq_path, seq_info["frame_list"]))

        return frame_sequences
