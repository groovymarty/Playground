# bodyhelper

class BodyHelper:
    maxIndex = 100

    @staticmethod
    def join_key(*parts):
        return ".".join(parts)

    @staticmethod
    def make_flavored(flavor, d):
        return {BodyHelper.join_key(flavor, key): value for key, value in d.items()}
