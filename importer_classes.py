import pye57
import numpy as np

class Scan:
    def __init__(self, scan_index, e57_file):
        self.scan_index = scan_index
        self.e57_file = e57_file
        self.scan_name = None
        self.points_local = None
        self.camera_location = None
        self.camera_rotation = None
        self.points_global = None
        self.points_colors = None

    def process_scan(self):
        data = self.e57_file.read_scan_raw(self.scan_index)
        header = self.e57_file.get_header(self.scan_index)

        self.scan_name = header.node['name'].value()
        self.points_local = np.column_stack([
            data['cartesianX'],
            data['cartesianY'],
            data['cartesianZ'],
        ])

        self.camera_location = header.translation
        self.camera_rotation = header.rotation
        self.points_global = self.e57_file.to_global(
            self.points_local, header.rotation, header.translation)

        if 'colorRed' in data:
            self.points_colors = np.column_stack([
                data['colorRed'],
                data['colorGreen'],
                data['colorBlue'],
            ]).astype(np.uint8)

class E57Reader:
    def __init__(self, filepath):
        self.filepath = filepath
        self.scans = []
        self.has_colors = False

    def read_scans(self):
        with pye57.E57(self.filepath, 'r') as e57:
            num_scans = e57.scan_count
            for scan_index in range(num_scans):
                scan = Scan(scan_index, e57)
                scan.process_scan()
                self.scans.append(scan)
                if scan.points_colors is not None:
                    self.has_colors = True
