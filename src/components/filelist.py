class FileList:
    def __init__(self, files: list[str]):
        self.files = files

    def __str__(self):
        return "\n".join(self.files)