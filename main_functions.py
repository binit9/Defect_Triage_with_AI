# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 10:57:05 2019

@author: hussain.m.boxwala
"""
import utility as ut
import en_core_web_lg
model = en_core_web_lg.load()

def clean_data(df):
    print("cleaning data")
    df1 = df.copy()
    df_abbrv = ut.read_file(r'keyword database - AI solution.xlsx', sheet_name = 'Abbreviations')
    df1 = ut.replace_abbvr(df_abbrv,df1,"defect_description", "replaced_text")
    df1 = ut.remove_extras(df1, "replaced_text", "reduced_text")
    df1 = ut.preprocess(df1, "reduced_text", "cleaned_text")
    df1 = ut.get_unique(df1, "cleaned_text", "unique_description")
    return df1


def predict_duplicate(base_df, delta_df, input_col="unique_description"):
    state_list = ['o - submitted','r - submitted','o - assigned','r - assigned','o - implemented','r - implemented']
    base_df = base_df[base_df["state"].str.lower().isin(state_list)]
    df_kywrd = ut.read_file(r'keyword database - AI solution.xlsx', sheet_name = 'Key Terminology')
    df_kywrd = ut.preprocess(df_kywrd, "Terminology", "cleaned_keyword")
    df_kywrd['factor'] = df_kywrd['Weightage (High/ Medium/ Low)'].map(ut.assign_val)
    factor = list(df_kywrd['factor'])
    keywords = []
    for index, rows in df_kywrd.iterrows():
        keywords.append(rows['cleaned_keyword'])
    key_val = {}
    for i in range(len(keywords)):
        key =keywords[i]
        factor_val = factor[i]
        key_val[key]=factor_val

    result = ut.prediction(base_df, delta_df, input_col, keywords, key_val, model)
    return result