def rgb(image):
    import cv2
    
    # Convert the numpy array to uint8 as to be able to convert the color
    cv2_compatible_image = image.astype('uint8')

    # OpenCV images are in BGR, meanwhile pyplot expects RGB,
    rgb_image = cv2.cvtColor(cv2_compatible_image, cv2.COLOR_BGR2RGB)

    return rgb_image


# +
from pathlib import Path
from typing import List

def get_all_videos_in_directory(directory: Path) -> List[str]:
    all_files = [f for f in directory.iterdir()]
    
    all_files = filter(lambda f: f.suffix != '.md', all_files)
    all_files = filter(lambda f: f.suffix != '.txt', all_files)
    
    videos = [str(f) for f in all_files]
    videos.sort()

    return videos


# +
from typing import List

def get_all_videos() -> List[str]:
    import os

    uploads_directory = Path('static/videos/uploads')
    archive_directory = Path(os.environ['VIDEO_DIRECTORY'])
    output_directory = Path(os.environ['OUTPUT_DIRECTORY'])
    
    uploads = get_all_videos_in_directory(uploads_directory)
    reference = get_all_videos_in_directory(archive_directory)
    outputs = get_all_videos_in_directory(output_directory)
    
    return uploads + reference + outputs


# -

def video_selector(select_multiple=False, default=None):
    import ipywidgets as widgets
    from ipywidgets import Layout

    layout = {'width': 'max-content'}
    
    if select_multiple:
        return widgets.SelectMultiple(
            options=get_all_videos(),
            value=default,
            description='Video:',
            disabled=False,
            layout=layout
        )

    return widgets.Select(
        options=get_all_videos(),
        description='Video:',
        value=default,
        disabled=False,
        layout=layout
    )


# +
from video_reuse_detector.keyframe import Keyframe

def plot_keyframe(ax, keyframe: Keyframe):
    ax.imshow(keyframe.image)
    ax.axis('off')


# -

def plot_stacked_color_correlation(axs, query_fingerprint, reference_fingerprint):
    import numpy as np
    from video_reuse_detector.color_correlation import CORRELATION_CASES
    from matplotlib import pyplot as plt

    query_cc = query_fingerprint.color_correlation
    reference_cc = reference_fingerprint.color_correlation

    indices = np.arange(len(CORRELATION_CASES))

    axs.bar(indices, list(query_cc.histogram.values()), color="orangered", alpha=0.5)
    axs.bar(indices, list(reference_cc.histogram.values()), color='mediumslateblue', alpha=0.5)
        
    plt.sca(axs)
    plt.tick_params(
        axis='y',          # changes apply to the y-axis
        which='both',      # both major and minor ticks are affected
        left=False,        # ticks along the left edge are off
        right=False,       # ticks along the right edge are off
        labelleft=False)   # labels along the left edge are off        
    plt.xticks(indices, CORRELATION_CASES, rotation='vertical')


# +
def plot_color_correlation(axs, color_correlation):
    import numpy as np
    from video_reuse_detector.color_correlation import CORRELATION_CASES
    from matplotlib import pyplot as plt

    indices = np.arange(len(CORRELATION_CASES))

    axs.bar(indices, color_correlation.histogram.values())
    plt.sca(axs)
    plt.tick_params(
        axis='y',          # changes apply to the y-axis
        which='both',      # both major and minor ticks are affected
        left=False,        # ticks along the left edge are off
        right=False,       # ticks along the right edge are off
        labelleft=False)   # labels along the left edge are off  
    plt.xticks(indices, CORRELATION_CASES, rotation='vertical')

def plot_color_correlation_from_keyframe(axs, keyframe):
    from video_reuse_detector.color_correlation import ColorCorrelation

    color_correlation = ColorCorrelation.from_image(keyframe.image)
    return plot_color_correlation(axs, color_correlation)


# -

def display_video(selection):
    from IPython.display import Video
    from pathlib import Path

    # TODO: Handle when selection is an abs-path
    try:
        # selection is an absolute path and Video expects
        # a relative path
        rel_path = str(Path.cwd().relative_to(selection))
    except ValueError as e:
        # a relative path was given
        rel_path = selection
    
    display(f'Displaying "{rel_path}"')

    return Video(rel_path)
