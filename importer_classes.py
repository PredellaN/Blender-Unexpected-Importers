import pye57, numpy as np

class E57Reader:
    def __init__(self, filepath):
        self.filepath = filepath
        
        self.scans = []

        self.has_colors = False

    def read_scans(self):
        with pye57.E57(self.filepath, 'r') as e57:
            num_scans = e57.scan_count

            for scan_index in range(num_scans):
                scan_data = {}

                data = e57.read_scan_raw(scan_index)
                header = e57.get_header(scan_index)

                scan_data['points_local'] = np.column_stack([
                        data['cartesianX'],
                        data['cartesianY'],
                        data['cartesianZ'],
                ])

                scan_data['camera_location'] = header.translation
                scan_data['camera_rotation'] = header.rotation
                scan_data['points_global'] = e57.to_global(scan_data['points_local'], header.rotation, header.translation)

                if 'colorRed' in data:
                    self.has_colors = True
                    scan_data['points_colors'] = np.column_stack([
                        data['colorRed'],
                        data['colorGreen'],
                        data['colorBlue'],
                    ]).astype(np.uint8)

            self.scans.append(scan_data)