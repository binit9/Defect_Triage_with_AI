# -*- coding: utf-8 -*-
"""
Created on Mon Nov 18 11:44:32 2019

@author: ankita.bu.singh
"""
import pandas as pd
import numpy as np
import Data_cleaning as dc
import operator
import re

#reading the excel
def read_file(name, sheet_name = 'Sheet1'):
    df = pd.read_excel(name, sheet_name, keep_default_na=False, na_values=["__"])
    return df

#Replacing abbreviations
def replace_abbvr(df_abbrv, df_toreplace, input_col, out_col):
    print("replacing abbreviations")
    df_temp = df_toreplace.copy()
    for index1, rows1 in df_temp.iterrows():
        desc = str(rows1[input_col])
        for index2, rows2 in df_abbrv.iterrows():
            short_names = " " +str(rows2['alternative spelling/ longform'])
            full_names = " " +str(rows2['keyword'])
            flag = str(rows2["is_abbrv"])
            if(flag == 'yes'):
                desc = desc.replace(short_names, full_names)
            else:
                desc = desc.lower().replace(short_names.lower(),full_names.lower())
        df_temp.loc[index1, out_col] = desc
    return df_temp

#Removing contents after steps to reproduce and configuration as it is not adding much value to description.
def remove_extras(df, input_col, out_col):
    print("removing extras")
    temp = df.copy()
# =============================================================================
#     temp = temp.filter(["ID","Title","Description HTML","HPQC ID (Roche)",
#                                "HPQC Rejection Reason (Roche)", "State",
#                                "Affected Version for Issue (Roche)" , input_col])
# =============================================================================
    temp[input_col] = temp[input_col].replace("\n", " ", regex=True)
    temp["combined_text"] = temp["title"].map(str) + " " + temp[input_col].map(str)
    temp["combined_text"]  = temp["combined_text"] .str.lower()
    indexes_of_step = []
    temp[out_col] = ""
    temp["category"] = ""
    for index, row in temp.iterrows():
        text = row["combined_text"]
        temp.loc[index, "category"] = row["affected_version"].split("_")[0]
        if "steps to rep" in text:
            indexes_of_step.append(index)
            start = re.search("steps to rep", text).span()[0]
            temp.loc[index, out_col] = text[:start]
        elif "steps to execute" in text:
            indexes_of_step.append(index)
            start = re.search("steps to execute", text).span()[0]
            temp.loc[index, out_col] = text[:start]
        elif "steps to test" in text:
            indexes_of_step.append(index)
            start = re.search("steps to test", text).span()[0]
            temp.loc[index, out_col] = text[:start]
        elif "reproduction steps" in text:
            indexes_of_step.append(index)
            start = re.search("reproduction steps", text).span()[0]
            temp.loc[index, out_col] = text[:start]
        else:
            temp.loc[index, out_col] = text
    count1 = 0
    count2 = 0         
    for index, row in temp.iterrows():
        text = row[out_col]
        if re.search("config[\w/]*:", text):
            indexes_of_step.append(index)
            start = re.search("config[\w/]*:", text).span()[0]
            temp.loc[index, out_col] = text[:start]
            count1 += 1
            count2 += 1
            if count2 % 100==0:
                print('for',count1, 'running', count2)
        else:
            temp.loc[index, out_col] = text
            
    for index, row in temp.iterrows():
        text = row[out_col]
        if re.search("[n\s]configuration\s", text):
            indexes_of_step.append(index)
            start = re.search("[n\s]configuration\s", text).span()[0]
            temp.loc[index, out_col] = text[:start]
        else:
            temp.loc[index, out_col] = text
            
    return temp

#Function to clean the text or description.
def preprocess(df, input_col, out_col):
    print("preprocess cleaning")
    temp = df.copy()
    for index, row in temp.iterrows():
        raw_text = str(row[input_col])
        cleaned_text = dc.stop_and_stem(dc.text_clean(raw_text), stem = False)
        temp.loc[index, out_col] = cleaned_text
    return temp

#Function to keep the first occurrence of words only.
def get_unique(df, input_col, out_col):
    print("creating unique")
    temp = df.copy()
    for index, row in temp.iterrows():
        text = str(row[input_col])
        text = text.lower()
        slist = text.split()
        text = " ".join(sorted(set(slist), key = slist.index))
        temp.loc[index, out_col] = text
    return temp

#assigning weightage to keywords
def assign_val(var):
    var = var.lower()
    if(var == "high"):
        val = 12
    elif(var == "medium"):
        val = 8
    else:
        val = 4
    return val

#Function to assign weightage and calculate the cosine similarity.
def prediction(base_data, test_data, input_col, kywrd_list, key_factor, model):
    
    def text_to_vec_test(text, kywrd_list):
        defect_master_dict = {}
        for kw in kywrd_list:
            if len(kw.split())==1:
                if kw in text.split():
                    if kw not in defect_master_dict.keys():
                        defect_master_dict[kw] = key_factor[kw]
            else:
                for item in kw.split():
                    counter = 0
                    if item in text.split():
                        counter+=1
                if counter == len(kw.split()):
                    for item in kw.split():
                        if item not in defect_master_dict.keys():
                            defect_master_dict[item] = key_factor[kw]
        print(defect_master_dict)               
        vec = text_to_vec(text, defect_master_dict)
        return vec, defect_master_dict
    
    def text_to_vec(text, kywrd_dict):
        vector = []
        words = text.split()
        for word in words:
            single_vec = model(word).vector
            if word in kywrd_dict.keys():
                single_vec = single_vec * int(kywrd_dict[word])
            vector.append(single_vec)
        num_vec = len(vector)
        avg_vec = sum(vector)/ num_vec
        return avg_vec


    def cos_sim(vec1,vec2):
        #key_subset = [word for word in kywrd_list if word in text1]
        dot_product = np.dot(vec1, vec2)
        norm_1 = np.linalg.norm(vec1)
        norm_2 = np.linalg.norm(vec2)
        return dot_product / (norm_1 * norm_2)
    print("Predictions started")
    all_ids = []
    predicted_duplicate_id = []
    top_5_id = []
    top_5_score = []
    max_scores = [] 
    count1 = 0
    
    #Calling similarity function to see which Test Id is matching to different other Test Id with similarity score greater than 97%.
    from datetime import datetime
    start_time_1 = datetime.now()
    for index1, rows1 in test_data.iterrows():
        start_time_2 = datetime.now()
        cat1 = rows1['category'].split('_')[0]
        if cat1 != "-":
            new_df = base_data[base_data['category'] == cat1]
        else:
            new_df = base_data
        count1 += 1
        count2 = 0
        Id = rows1['id']
        all_ids.append(Id)
        #print(all_ids)
        scores_dict = {}      
        #for index2, rows2 in df_original_ref.iterrows():
        vec1, key_subset = text_to_vec_test(rows1[input_col], kywrd_list)
        for index2, rows2 in new_df.iterrows():
            #if row2['category'] == cat1:
            count2 += 1
            #print(count1,count2)
            if count2 % 100==0:
                print('for',count1, 'running', count2)
                print(datetime.now() - start_time_2)
                
            compare_id = rows2['id']
            if Id!=compare_id:
                vec2 = text_to_vec(rows2[input_col], key_subset)
                score = cos_sim(vec1, vec2)
                scores_dict.update({compare_id:score})
    
        max_value = max(scores_dict.values())
        sorted_scores_dict = dict(sorted(scores_dict.items(), key=operator.itemgetter(1), reverse=True))
        top_5_score.append(list(sorted_scores_dict.values())[:5])
        top_5_id.append(list(sorted_scores_dict.keys())[:5])
        predicted_id = list(scores_dict.keys())[list(scores_dict.values()).index(max_value)]
        predicted_duplicate_id.append(predicted_id)
        max_scores.append(max_value)
        print(all_ids[-1],max_scores[-1],predicted_duplicate_id[-1])
        
    print(datetime.now() - start_time_1)
    new = pd.DataFrame(list(zip(all_ids,max_scores,top_5_score,top_5_id,predicted_duplicate_id)),
                   columns =['Id','max_scores','top_5_score','top_5_id','predicted_duplicate_id'])
    return new

