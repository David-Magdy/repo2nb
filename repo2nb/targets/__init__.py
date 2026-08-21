from . import colab, kaggle

TARGETS = {"kaggle": kaggle, "colab": colab}


def get_target(name: str):
    return TARGETS[name]
