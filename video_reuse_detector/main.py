from pathlib import Path
from typing import Dict, List

from loguru import logger

import video_reuse_detector.util as util
from video_reuse_detector.fingerprint import (
    FingerprintCollection,
    FingerprintComparison,
)
from video_reuse_detector.keyframe import Keyframe
from video_reuse_detector.profiling import timeit


def list_keyframe_paths(
    directory: Path, glob_pattern: str = '**/keyframe.png'
) -> List[Path]:
    keyframe_paths = list(directory.glob(glob_pattern))

    logger.debug(
        f'Found {len(keyframe_paths)} keyframes under "{directory}" (glob_pattern="{glob_pattern}")'  # noqa: E501
    )
    return keyframe_paths


# segment_id -> keyframe
def load_keyframes(directory: Path) -> Dict[int, Keyframe]:
    images = {}

    for path in list_keyframe_paths(directory):
        segment_id = util.segment_id_from_path(path)
        keyframe_image = util.imread(path)

        images[segment_id] = Keyframe(keyframe_image)

    return images


def fingerprint_collection_from_directory(directory: Path):
    keyframes = load_keyframes(directory)
    video_name = directory.stem
    fingerprints = []

    for segment_id, keyframe in keyframes.items():
        fp = FingerprintCollection.from_keyframe(
            keyframe, video_name, segment_id
        )  # noqa: E501
        fingerprints.append(fp)

    return fingerprints


@timeit
def compute_similarity_between(
    query_fingerprints_directory: Path, reference_fingerprints_directory: Path
):
    query_fps = fingerprint_collection_from_directory(
        query_fingerprints_directory
    )  # noqa: E501
    reference_fps = fingerprint_collection_from_directory(
        reference_fingerprints_directory
    )  # noqa: E501

    return FingerprintComparison.compare_all(query_fps, reference_fps)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Video reuse detector')

    parser.add_argument(
        'query_fingerprints_directory', help='A directory with fingerprints'
    )

    parser.add_argument(
        'reference_fingerprints_directory', help='Another directory with fingerprints'
    )

    args = parser.parse_args()

    query_directory = Path(args.query_fingerprints_directory)
    logger.debug(f'Treating "{query_directory}" as the query "video"')

    reference_directory = Path(args.reference_fingerprints_directory)
    logger.debug(f'Treating "{reference_directory}" as the reference "video"')

    similarities = compute_similarity_between(query_directory, reference_directory)

    for segment_id, sorted_comparisons in similarities.items():
        id_to_similarity_score_tuples = [
            (c.reference_segment_id, c.similarity_score) for c in sorted_comparisons
        ]  # noqa: E501
        print(segment_id, id_to_similarity_score_tuples[:5])
