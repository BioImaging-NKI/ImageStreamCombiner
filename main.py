import argparse
from pathlib import Path
import logging
from combine_imagestream_files import ImageStreamZip


def get_args() -> argparse.Namespace:
    """
    Get the arguments from the commandline
    :return:
    """
    myparser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    myparser.add_argument(
        "-i",
        type=str,
        help="The input zipfile.",
        default="",
    )
    myparser.add_argument(
        "-p",
        type=float,
        help="Pixelsize",
        default=1.0,
    )
    myparser.add_argument(
        "-l",
        type=str,
        help="LogLevel: 0 error (default), 1 warning, 2 info",
        default=0,
    )
    return myparser.parse_args()


if __name__ == "__main__":
    args = get_args()
    loglevels = [logging.ERROR, logging.WARNING, logging.INFO]
    loglevel = loglevels[int(args.l)]
    logging.basicConfig(level=loglevel)
    logging.info("Arguments parsed")
    logging.info(f"Loglevel: {logging.getLevelName(loglevel)}")
    zipin = Path(args.i)
    runit = False
    if not zipin.exists() or not zipin.is_file():
        print(f"Cannot find zipfile: {args.i}")
    else:
        isz = ImageStreamZip()
        isz.loadfile(zipin)
        isz.writetiffs(zipin.parent, args.p)
