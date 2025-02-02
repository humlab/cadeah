import shutil
from pathlib import Path
from typing import List

from loguru import logger

from video_reuse_detector import ffmpeg


# TODO: Remove this one or the one in util
def get_segment_id(path: Path) -> str:
    """
    >> get_segment_id(Path('interim/dive/dive-segment013.mp4'))
    '013'
    """
    return path.stem[-3:]


def segment(
    input_video: Path, output_directory: Path, segment_length_in_seconds=1
) -> List[Path]:
    if not input_video.exists():
        logger.warning(
            f'input_video={input_video} does not exist! Producing an empty list'
        )
        return []

    # -i                     input file
    # -codec:v libx264       re-encode so we can force keyframes
    # -force_key_frames      force keyframe every x seconds
    # -map 0                 use the given input file to produce all outputs
    # -f segment             output file will be multiple segments
    # -segment_time          length of each segment expressed in seconds
    ffmpeg_cmd = (
        'ffmpeg'
        f' -i {input_video}'
        f' -force_key_frames expr:gte(t,n_forced*{segment_length_in_seconds})'
        ' -map 0'
        ' -f segment'
        f' -segment_time {segment_length_in_seconds}'
        ' -vcodec copy'
        f' {output_directory}/{input_video.stem}-segment%03d{input_video.suffix}'
    )

    logger.info(f'Segmenting "{input_video}"')
    segment_paths = ffmpeg.execute(ffmpeg_cmd, output_directory)
    logger.trace(f'Produced {list(map(str, segment_paths))}')

    written_files = []

    # TODO: Document or remove this step
    logger.trace('Restructuring output...')

    for path in segment_paths:
        target_directory = output_directory / f'segment/{get_segment_id(path)}'
        target_directory.mkdir(parents=True, exist_ok=True)

        # Note .suffix contains the "."
        dst = target_directory / f'video{path.suffix}'
        written_files.append(dst)

        logger.trace(f'Moving "{path}" to "{dst}"')
        shutil.move(path, dst)

    logger.trace(
        f'Segmenting produced output="{list(map(str, written_files))}"'
    )  # noqa: E501

    return written_files


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Video segmentation')

    parser.add_argument('input_video', help='The video to segment')

    parser.add_argument('output_directory', help='A directory to write the outputs to')

    args = parser.parse_args()

    outputs = segment(Path(args.input_video), Path(args.output_directory))

    print(*outputs, sep='\n')
