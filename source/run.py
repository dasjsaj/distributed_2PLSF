"""Run All Experiments"""
import os
import sys
import time
import argparse
import pathlib
import tomllib
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt


parser = argparse.ArgumentParser(description='Run all experiments in 2PLSF')
parser.add_argument('-c', '--config', type=pathlib.Path, default='config.toml',
                    help='Config file path.')


def benchmarks(run_config: dict):
    """
    Run all benchmarks
    """
    print('\n\n+++ Running microbenchmarks +++\n')

    # Log directory
    if not pathlib.Path('data').is_dir():
        os.mkdir('data')

    # Binary file directory
    bin_folder = run_config['bin_folder']

    # List of threads to execute
    thread_list = ''
    for i in run_config['thread_list']:
        thread_list += str(i) + ','
    thread_list = thread_list[:-1]

    # Write ratios in permils (100 means 10% writes and 90% reads)
    ratio_list = ''
    for i in run_config['ratio_list']:
        ratio_list += str(i) + ','
    ratio_list = ratio_list[:-1]

    stm_name_list = run_config['stm_name_list']
    cmd_line_options = f"--duration={run_config['time_duration']} \
        --runs={run_config['num_runs']} --threads={thread_list} --ratios={ratio_list}"

    # Run all experiments
    for stm in stm_name_list:
        os.system(f'{bin_folder}/set-ll-1k-{stm} {cmd_line_options} --keys=1000')
    for stm in stm_name_list:
        os.system(f'{bin_folder}/set-hash-10k-{stm} {cmd_line_options} --keys=10000')

    for stm in stm_name_list:
        os.system(f'{bin_folder}/set-ravl-1m-{stm} {cmd_line_options} --keys=1000000')
    for stm in stm_name_list:
        os.system(f'{bin_folder}/set-skiplist-1m-{stm} {cmd_line_options} --keys=1000000')
    for stm in stm_name_list:
        os.system(f'{bin_folder}/set-ziptree-1m-{stm} {cmd_line_options} --keys=1000000')
    for stm in stm_name_list:
        os.system(f'{bin_folder}/set-tree-1m-{stm} {cmd_line_options} --keys=1000000')
    for stm in stm_name_list:
        os.system(f'{bin_folder}/set-btree-1m-{stm} {cmd_line_options} --keys=1000000')

    # Specify ratio in map
    cmd_line_options = cmd_line_options[:cmd_line_options.find('--ratios')]
    for stm in stm_name_list:
        os.system(f'{bin_folder}/map-ravl-{stm} {cmd_line_options} --keys=100000 --ratios=1000')
    for stm in stm_name_list:
        os.system(f'{bin_folder}/map-skiplist-{stm} {cmd_line_options} --keys=100000 --ratios=1000')
    for stm in stm_name_list:
        os.system(f'{bin_folder}/map-ziptree-{stm} {cmd_line_options} --keys=100000 --ratios=1000')

    # Benchmark with the latency measures
    for stm in stm_name_list:
        os.system(f'{bin_folder}/part-disjoint-{stm} {cmd_line_options} >> data/latency.log 2>&1')

    # Test algorithm
    db_algo = ['TICTOC', 'NO_WAIT', 'DL_DETECT', 'TWO_PL_SF']
    db_config_file = 'DBx1000/config.h'

    for algo in db_algo:
        # modify & compile
        with open(db_config_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            if '#define CC_ALG' in line:
                lines[i] = f'#define CC_ALG {algo}\n'
        with open(db_config_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        os.system('cd DBx1000 && make')  # -j

        # "High contention", from page 1637 of https://dl.acm.org/doi/pdf/10.1145/2882903.2882935
        os.system('echo "Threads\tTransactions\tTime" > data/ycsb-high-' + algo.lower() + '.txt')

        for thread in run_config['thread_list']:
            os.system(f'cd DBx1000 && ./rundb -o output.txt -t{thread} -r0.5 -w0.5 -R16 -z0.9')
            os.system(f'cat DBx1000/output.txt >> data/ycsb-high-{algo.lower()}.txt')
            time.sleep(1)

        # "Medium contention"
        os.system('echo "Threads\tTransactions\tTime" > data/ycsb-med-' + algo.lower() +  '.txt')
        for thread in run_config['thread_list']:
            os.system(f'cd DBx1000 && ./rundb -o output.txt -t{thread} -r0.9 -w0.1 -R16 -z0.8')
            os.system(f'cat DBx1000/output.txt >> data/ycsb-med-{algo.lower()}.txt')
            time.sleep(1)

        # "Low contention"
        os.system('echo "Threads\tTransactions\tTime" > data/ycsb-low-' + algo.lower() + '.txt')
        for thread in run_config['thread_list']:
            os.system(f'cd DBx1000 && ./rundb -o output.txt -t{thread} -r1.0 -w0 -R2 -z0')
            os.system(f'cat DBx1000/output.txt >> data/ycsb-low-{algo.lower()}.txt')
            time.sleep(1)

    print('\n\n+++ Running microbenchmarks done +++\n')


def data_plot(run_config: dict):
    """
    Plot
    """
    ratio_list = run_config['ratio_list']

    if not pathlib.Path('figure').is_dir():
        for i in range(5):
            os.makedirs(f'figure/exp_{i+1}')

    data_dir = 'data'
    file_lists = os.listdir(data_dir)
    data_structures = {i[:i.rfind('-')]: [] for i in file_lists}

    # Read data file
    for f in file_lists:
        if not f.endswith('.txt'):
            continue
        df = pd.read_csv(f'{data_dir}/{f}', sep='\t', encoding='utf-8', index_col=False)
        df = df.loc[:, ~df.columns.str.match('Unnamed')]
        structure = f[:f.rfind('-')]
        data_structures[structure].append(
            {'name': f[:f.find('.')], 'data': df}
        )

    # matplotlib global config
    mpl.rcParams.update({
        'font.size': 10,
        'figure.dpi': 600,
    })

    # "We also compared with Orec-eager and the results were similar to Orec-lazy,
    #  therefore we chose to show the later only."
    hidden_algo = ['2plundo', 'tl2orig', '2plundodist', 'oreceager']

    algo_marker = {
        '2plsf': 'gD',
        'two_pl_sf': 'gD',
        'tiny': 'bx',
        'tlrweager': 'r^',
        'ofwf': 'mv',
        'tl2': 'ko',
        'oreclazy': 'ys',

        '2plundo': 'bx',
        '2plundodist': 'r^',

        'tictoc': 'bx',
        'no_wait': 'r^',
        'dl_detect': 'mv',
    }

    structure_name = {
        'set-ll-1k': 'LinkedListSet with $10^3$ keys',
        'set-hash-10k': 'HashMap (fixed size) with $10^4$ keys',

        'set-btree-1m': 'BTree with $10^6$ keys',
        'set-ziptree-1m': 'ZipTree with $10^6$ keys',
        'set-skiplist-1m': 'SkipList with $10^6$ keys',
        'set-ravl-1m': 'Relaxed AVL with $10^6$ keys',
        'set-tree-1m': 'RedBlackTree with $10^6$ keys',

        'map-skiplist-98u-100k': 'SkipList with $10^5$ keys',
        'map-ravl-98u-100k': 'Relaxed AVL with $10^5$ keys',
        'map-ziptree-98u-100k': 'ZipTree with $10^5$ keys',
    }

    # 3.1 Different RW-Locks
    values = data_structures['set-ravl-1m']
    total_idx = len(ratio_list)  # write ratios

    fig, axs = plt.subplots(1, total_idx, figsize=[13.5, 4.5])
    fig.suptitle(structure_name['set-ravl-1m'])
    fig.supxlabel('Number of threads')
    fig.supylabel(r'Operations ($\times 10^6$ /s)')
    fig.tight_layout()

    for i, a in enumerate(axs):
        a.set_title(f'{ratio_list[i] / 10}% write')

    for v in values:
        if '2pl' in v['name']:
            data = v['data']
            name = v['name']
            name = name[name.rfind('-')+1:]

            x = data['Threads']

            for idx in range(total_idx):
                y = data[data.keys()[idx+1]]  # first column is `Threads`
                y = [round(num / 1e6, 2) for num in y]  # 10^6 /s

                axs[idx].plot(x, y, algo_marker[name], label=name.upper(),
                                linestyle='-' if name == '2plsf' else '--')

    plt.subplots_adjust(left=0.07, bottom=0.1)
    plt.legend()
    plt.savefig('figure/exp_1/2pl_set-ravl-1m')

    for structure, values in data_structures.items():
        # 3.2 Set Data Structures
        if 'set' in structure:
            total_idx = len(ratio_list)  # write ratios

            fig, axs = plt.subplots(1, total_idx, figsize=[13.5, 4.5])
            fig.suptitle(structure_name[structure])
            fig.supxlabel('Number of threads')
            fig.supylabel(r'Operations ($\times 10^6$ /s)')
            fig.tight_layout()

            for i, a in enumerate(axs):
                a.set_title(f'{ratio_list[i] / 10}% write')

            for i, content in enumerate(values):
                data = content['data']
                name = content['name']
                name = name[name.rfind('-')+1:]

                if name in hidden_algo:
                    continue

                x = data['Threads']

                for idx in range(total_idx):
                    y = data[data.keys()[idx+1]]  # first column is `Threads`
                    y = [round(num / 1e6, 2) for num in y]  # 10^6 /s

                    axs[idx].plot(x, y, algo_marker[name], label=name.upper(),
                                  linestyle='-' if name == '2plsf' else '--')

            plt.subplots_adjust(left=0.07, bottom=0.1)
            plt.legend()
            plt.savefig('figure/exp_2/' + structure)

        # 3.3 Map Data Structures
        elif 'map' in structure:
            # Maps only have one ratio
            fig, ax = plt.subplots(figsize=[6.4, 4.8])

            ax.set_title(f'{structure_name[structure]} (10% insert, 10% remove, 98% update)')
            ax.set_xlabel('Number of threads')
            ax.set_ylabel(r'Operations ($\times 10^6$ /s)')

            for i, content in enumerate(values):
                data = content['data']
                name = content['name']
                name = name[name.rfind('-')+1:]

                if name in hidden_algo:
                    continue

                x = data['Threads']

                y = data[data.keys()[1]]
                y = [round(num / 1e6, 2) for num in y]

                ax.plot(x, y, algo_marker[name], label=name.upper(),
                        linestyle='-' if name == '2plsf' else '--')

            plt.legend()
            plt.savefig('figure/exp_3/' + structure)

        # 3.4 Tail Latency
        elif 'part' in structure:
            fig, ax = plt.subplots(figsize=[6.4, 4.8])

            for i, content in enumerate(values):
                data = content['data']
                name = content['name']
                name = name[name.rfind('-')+1:]

                if name in hidden_algo:
                    continue

                x = data['Threads']

                y = data[data.keys()[1]]
                y = [round(num / 1e3, 2) for num in y]

                ax.plot(x, y, algo_marker[name], label=name.upper(),
                        linestyle='-' if name == '2plsf' else '--')

                ax.set_title('Throughput for pair-wise conflicts')
                ax.set_xlabel('Number of threads')
                ax.set_ylabel(r'Throughput ($\times 10^3$ txn/s)')

            plt.legend()
            plt.savefig('figure/exp_4/' + structure)

        # 3.5 YCSB in DBx1000
        elif 'ycsb' in structure:
            fig, ax = plt.subplots(figsize=[6.4, 4.8])

            if 'high' in structure:
                ax.set_title('YCSB with High contention 50%w 50%r')
            elif 'med' in structure:
                ax.set_title('YCSB with Medium contention 10%w 90%r')
            elif 'low' in structure:
                ax.set_title('YCSB with Low contention 0%w 100%r')

            ax.set_xlabel('Number of threads')
            # About 100000 txn per thread
            ax.set_ylabel('Run Time (s)')

            for i, content in enumerate(values):
                data = content['data']
                name = content['name']
                name = name[name.rfind('-')+1:]

                x = data['Threads']
                y = data['Time']

                ax.plot(x, y, algo_marker[name], label=name.upper(),
                        linestyle='-' if name == 'two_pl_sf' else '--')

            plt.legend()
            plt.savefig('figure/exp_5/' + structure)


if __name__ == '__main__':
    # Parse config file
    args = parser.parse_args()

    if not args.config.exists():
        print(f'No such file {args.config}!')
        sys.exit(-1)

    with args.config.open('rb') as config_file:
        config = tomllib.load(config_file)

    benchmarks(config)

    data_plot(config)
