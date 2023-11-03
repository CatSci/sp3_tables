import pandas as pd
import streamlit as st
import numpy as np
from collections import OrderedDict
import math


def read_rt(file, sheet_name):
    """Return a list

    extract all retention time from different time reaction
    """
    rt_list = []
    for i in sheet_name:
        df = pd.read_excel(file , sheet_name = i)
        rt_col = df['RT']
        rt_list.append(rt_col)
    
    rt = [i for sub_list in rt_list for i in sub_list]
    return rt

def add_rrt(dataframe):
    """Return a dataframe

    add rrt column in dataframe
    """
    max_area = dataframe['Total Area %'].max()
    rt_max = dataframe['Total Area %'].idxmax()
    dataframe['RRT'] = dataframe['RT'] / dataframe['RT'].iloc[rt_max]
    
    return dataframe

def fill_rrt(file, sheets, df):
    """Returns a dataframe

    fill the rrt value in dataframe
    """
    for i in sheets:
        d = pd.read_excel(file, sheet_name = i)
        row = d.shape[0]
        d = add_rrt(d)        # dataframe with rrt column
        for x in range(d.shape[0]):
            rrt_val = d.loc[x, 'RRT']  # rrt_value
            rt_val = d.loc[x, 'RT']
            idx = df.index[(df["RT"]== rt_val)]     # find index position for rt value in sp3
            df.iloc[idx, 1] = rrt_val

    return df

def add_data(file, sheets, dataframe):
    """Return a dataframe

    add data from different screen reaction time
    """
    
    for i in sheets:
        d = pd.read_excel(file, sheet_name = i)
        dataframe[i] = pd.DataFrame([[np.nan]], index = dataframe.index)
        # st.write(i)
        # st.write(dataframe)
        for idx, val in d.iterrows():
            area, rt_val = val['Total Area %'], val['RT']
            dataframe.at[dataframe.index[dataframe.RT == rt_val].tolist()[0], str(i)] = area
            # st.write(dataframe)
    
    return dataframe



def filter_data(dataframe: pd.DataFrame, start_retention: float, last_retention: float, area_threshold: float):
    """To split data into Under Threshold and Over Threshold excel files 

    Args:
        dataframe (pd.DataFrame): _description_
        start_retention (float): _description_
        last_retention (float): _description_

    Returns:
        dataframe: over_threshold_df, under_threshold_df
    """
    filtered_df = dataframe[(dataframe['RT'] >= start_retention) & (dataframe['RT'] <= last_retention)]
    
    columns = list(filtered_df.columns)
    over_threshold_df = pd.DataFrame(columns=columns)  # DataFrame for rows that satisfy the condition
    under_threshold_df = pd.DataFrame(columns=columns)  # DataFrame for rows that don't satisfy the condition
    
    for r in range(filtered_df.shape[0]):
        row = filtered_df.iloc[r]
        # st.write(row)
        if any(row[c] > area_threshold for c in columns if c not in ['RT', 'RRT']):
            over_threshold_df = pd.concat([over_threshold_df, pd.DataFrame([row])], ignore_index=True)
        else:
            under_threshold_df = pd.concat([under_threshold_df, pd.DataFrame([row])], ignore_index=True)
    # Drop rows in u_df that are also in f_df
    under_threshold_df = under_threshold_df[~under_threshold_df.apply(tuple, axis=1).isin(over_threshold_df.apply(tuple, axis=1))].reset_index(drop=True)
    
    # Reset the index for both dataframes
    over_threshold_df.reset_index(drop=True, inplace=True)
    
    
    return over_threshold_df, under_threshold_df


def find_same_col(df_file):
    """Return a dictionary
    to find if the two nearby values of retention time is almost same or not
    if its the same we need to drop it

    Args:
        df_file (_type_): _description_

    Returns:
        same_col: dictionary
    """
    same_col = {}
    for i in range(df_file.shape[1] - 2):
        x = df_file.iloc[0, i + 1]
        y = df_file.iloc[0, i + 2]
        if y - x <= 0.05:
            same_col[i + 2] = y
        else:
            pass

    return same_col

def drop_col(df, col): 
    """ Return a dataframe and the values of the column we need to drop
    to extract similar column values and drop the column

    Args:
        df (_type_): _description_
        col (_type_): _description_

    Returns:
        dataframe: dataframe after dropping columns
        col_to_drop: column value in a dictionary which are dropped
    """

    col_to_drop = {}
    for i in range(df.shape[0] - 1):
        p = df.iloc[i + 1, col]
        t = i + 1
        col_to_drop[t] = p
    
    # drop that column
    df.drop([col - 1], axis = 1, inplace = True)
    return df , col_to_drop


def replace_val(df, drop_col_val, col = 112):
    """Return a dataframe

    to replace the value in nearby column 
    """
    for i in range(df.shape[0] - 1):
        if math.isnan(drop_col_val[i + 1]):
            continue
        else:
            # st.write(df.columns[0])
            # st.write(i)
            if df.loc[i + 1, "index"] == "RRT":
                if int(df.iloc[i + 1, col]) != 1:
                    df.iloc[i + 1, col] = drop_col_val[i + 1]
            else:
                # st.write("value check")    
                # st.write(drop_col_val[i + 1])
                # st.write("current value")
                # st.write(df.iloc[i + 1, col])
                if not pd.isna(df.iloc[i + 1, col]) and drop_col_val[i + 1] > df.iloc[i + 1, col]:
                    # st.write("else then if")
                    # st.write(drop_col_val[i + 1])
                    df.iloc[i + 1, col] = drop_col_val[i + 1]
                elif pd.isna(df.iloc[i + 1, col]):
                    df.iloc[i + 1, col] = drop_col_val[i + 1]
    return df

def compress_data(dataframe: pd.DataFrame):
    """To remove column which have RT value difference less than 0.05 and merge the values

    Args:
        dataframe (pd.DataFrame): _description_

    Returns:
        dataframe: final_df
    """
    n_df = find_same_col(df_file= dataframe)
    rev_dict = OrderedDict(reversed(list(n_df.items())))
    for key, value in rev_dict.items():
            new_df, col_to_drop = drop_col(df = dataframe, col = key)
            final_df = replace_val(df = new_df, drop_col_val = col_to_drop, col = key - 1)

    return final_df