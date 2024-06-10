import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def convert_excel(save_path, result):
    df = pd.DataFrame(result, columns = ['query', 'rank-1', 'rank-2', 'rank-3'])
    #df = pd.DataFrame(result, columns = ['alpha', 'beta', 'rank-1', 'rank-2', 'rank-3'])
    df.to_excel(save_path)

def plot_heatmap(output):
    df = pd.DataFrame(output, columns = ['alpha', 'beta', 'rank-1', 'rank-2', 'rank-3'])
    pivot_data = df.pivot('beta', 'alpha', 'rank-1')
    sns.heatmap(pivot_data, cmap='coolwarm', annot=True)
    plt.show()

def plot_hist(x):
    plt.hist(x)
    plt.show()

def display_result(gt, all_output, alpha, beta):
    result = []
    count = rank1_count = rank2_count = rank3_count = 0
    all_output = pd.DataFrame(all_output)
    for x in range(len(all_output)):
        if str(all_output.iat[x, 0]) == 'nan':
                continue
        else:
            output_query = int(all_output.iat[x, 0])
        
        rank_1 = rank_2 = rank_3 = 0
        for y in range(1, 4):
            if (str(all_output.iat[x, y]) == 'NONE') or (str(all_output.iat[x, y]) == 'nan'):
                output_gallery = 'None'
            else:
                output_gallery = int(all_output.iat[x, y])
                
            gt_query = gt[gt['Query'] == output_query]
            gt_gallery = gt_query['Gallery']
            gt_list = gt_gallery.values.tolist()

            if 'None' in gt_list:
                continue
            count += 1
            if output_gallery in gt_list:
                if y == 1:
                    rank1_count += 1
                    rank_1 = 1
                elif y == 2 and rank_1 == 0:
                    rank2_count += 1
                    rank_2 = 2
                elif y == 3 and rank_1 == 0 and rank_2 == 0:
                    rank3_count += 1
                    rank_3 = 3
        result.append([output_query, all_output.iat[x, 1], all_output.iat[x, 2], all_output.iat[x, 3]])

    count = int(count/3) 
    print(f'{count}, {rank1_count}, rank-1: {rank1_count/count}, rank-2: {(rank1_count+rank2_count)/count}, rank-3: {(rank1_count+rank2_count+rank3_count)/count}')
    #alpha_beta.append([alpha, beta, rank1_count/count, (rank1_count+rank2_count)/count, (rank1_count+rank2_count+rank3_count)/count])
    return result
