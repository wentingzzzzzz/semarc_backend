
import argparse
import logging
import sys
from cluster_project import cluster_project
from settings import CACHE_PATH,DEFAULT_STOP_WORD_LIST

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(filename)s line: %(lineno)d] %(levelname)s - %(message)s",
    datefmt="[%Y-%m-%d %H:%M:%S]")
    
logger = logging.getLogger(__name__)
logging.getLogger('gensim').setLevel(logging.WARNING)
logging.getLogger('utils.utils').setLevel(logging.INFO)
logging.getLogger('project_file_manager.filename_convertor').setLevel(logging.INFO)


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Clustering software projects.')
    parser.add_argument('datapath',
        type=str, 
        nargs='+',
        help='path to the input project folder')
        
    parser.add_argument('-g', '--gt',
        metavar='',
        type=str, 
        nargs='+',
        help='path to the ground truth json file',
        default=None)

    parser.add_argument('-o', '--out_dir',
        metavar='',
        type=str, 
        help='path to the result folder',
        default=None)

    parser.add_argument('--cache_dir',
        metavar='',
        type=str, 
        help='cache path',
        default=CACHE_PATH)    
        
    parser.add_argument('-s', '--stopword_file',
        metavar='',
        nargs='+',
        type=str, 
        help='paths to external stopword lists',
        default=DEFAULT_STOP_WORD_LIST)
    
    parser.add_argument('-p', '--pattern_file',
        metavar='',
        nargs='+',
        type=str, 
        help='paths to architecture pattern files',
        default=None)
    
    parser.add_argument('-l', '--llm_file',
        metavar='',
        nargs='+',
        type=str, 
        help='paths to llm code summary files',
        default=None)

    parser.add_argument('-r', '--resolution',
        metavar='',
        type=float, 
        help='resolution parameter, affecting the final cluster size.',
        default=1.7)
    
    parser.add_argument('-n', '--no_fig',
        action='store_true', 
        help='prevent figure generation')

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()
        
    cluster_project(
        data_paths = args.datapath, 
        gt_json_paths = args.gt, 
        resolution = args.resolution, 
        result_folder_name = args.out_dir, 
        cache_dir = args.cache_dir,
        save_to_csvfile=True,
        stopword_files=args.stopword_file,
        fig_add_texts = [False],
        generate_figures = not args.no_fig,
        pattern_file = args.pattern_file,
        llm_file = args.llm_file
    )