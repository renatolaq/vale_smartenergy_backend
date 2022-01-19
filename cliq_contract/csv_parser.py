import pandas as pd 
import copy

def get_leaves(item, key=None):
    if isinstance(item, dict):
        leaves = {}
        for i in item.keys():
            leaves.update(get_leaves(item[i], i))
        return leaves

    elif isinstance(item, list):
        leaves = {}
        for i in item:
            leaves.update(get_leaves(i, key))
        return leaves

    else:
        # put formatting here
        if item == None:
            item = ""
            
        return {key : item}


def get_data_cliq_contract_csv(rest, mapping):

    final_df = []

    for aux in range(0, len(rest)):
        item = copy.deepcopy(rest[aux])
        
        body = get_leaves(item)
        pdbody = pd.DataFrame.from_dict([body])

        pdbody['key'] = aux

        merged_mult = pdbody
        
        for index, row in merged_mult.iterrows():
            data_peek = {}
            for a in mapping:
                try:
                    data_peek[a] = row[a]
                except:
                    data_peek[a] = ""
            final_df.append(data_peek)

    return final_df
