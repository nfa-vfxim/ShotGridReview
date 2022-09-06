"""This script functions
as a bridge between our Python script and the Deadline executable."""

import sys
from shotgrid_review import ShotGridReview

# Check before continue-ing to script
if len(sys.argv) != 10:
    print(
        "Usage: NUKE deadline_shotgrid_review_cli.py <first_frame> "
        "<last_frame> <fps> <publish_id> <sequence_path> <slate_path> "
        "<company> <colorspace_idt> <colorspace_odt>"
    )
    sys.exit(-1)

first_frame = int(sys.argv[1])
last_frame = int(sys.argv[2])
fps = float(sys.argv[3])
publish_id = int(sys.argv[4])
sequence_path = sys.argv[5]
slate_path = sys.argv[6]
company = sys.argv[7]
colorspace_idt = sys.argv[8]
colorspace_odt = sys.argv[9]

# ShotGrid credentials
shotgrid_site = "https://nfa.shotgunstudio.com"
script_name = "DeadlineReview"
script_key = "av$eejlrsBvrgqws4wcfchcam"

ShotGridReview(
    publish_id=publish_id,
    first_frame=first_frame,
    last_frame=last_frame,
    sequence_path=sequence_path,
    slate_path=slate_path,
    shotgrid_site=shotgrid_site,
    script_name=script_name,
    script_key=script_key,
    fps=fps,
    company=company,
    colorspace_idt=colorspace_idt,
    colorspace_odt=colorspace_odt,
)
