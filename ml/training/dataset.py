class CursiveDataset:
    def __init__(self, data_dir, split='train', transform=None):
        self.data_dir = data_dir
        self.split = split
        self.transform = transform

    def __len__(self):
        return 0

    def __getitem__(self, idx):
        return None
