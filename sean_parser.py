import xml.etree.ElementTree as ET


"""
<scenes>
<scene_1>[Brief description of the first scene]</scene_1>
<scene_2>[Brief description of the second scene]</scene_2>
...
</scenes>
"""

def parse_sean_tey(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    scenes = []
    for scene in root.findall('scene_*'):
        scenes.append(scene.text)
    return scenes
