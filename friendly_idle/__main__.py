from friendly_idle import patch_idle  # noqa


def main():
    import idlelib.pyshell

    idlelib.pyshell.main()


if __name__ == "__main__":
    main()
