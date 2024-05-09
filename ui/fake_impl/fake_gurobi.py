#!/usr/bin/env python
# coding: utf-8

# In[1]:


import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d


# In[2]:

def run():
    center_locations = pd.read_csv("fake_impl/center_location.csv", index_col="Center")
    landfill_locations = pd.read_csv("fake_impl/landfill_location.csv", index_col="Landfill")
    center_info = pd.read_csv("fake_impl/center_info.csv", index_col="Center")
    center_locations.head()
    landfill_locations.head()
    center_info.head()


    # In[3]:


    centers = list(center_locations.index)
    landfills = list(landfill_locations.index)


    # In[4]:


    sl_distance_centers_landfills = pd.DataFrame(index=centers, columns=landfills)
    for i in centers:
        for j in landfills:
            center_x = center_locations.loc[i, "x"]
            center_y = center_locations.loc[i, "y"]
            landfill_x = landfill_locations.loc[j, "x"]
            landfill_y = landfill_locations.loc[j, "y"]
            distance = ((center_x - landfill_x)**2 +
                        (center_y - landfill_y)**2)**(1/2)
            sl_distance_centers_landfills.loc[i, j] = distance


    # In[5]:


    # calculate big-M value
    bigM = max(center_info["waste tonnage"])

    # Create the model object (for question 1b)
    model_question1b = gp.Model("question1b_model")

    # Add the decision variables
    xcl = model_question1b.addVars(centers, landfills, name="xcl")
    z = model_question1b.addVars(landfills, vtype=GRB.BINARY, name="z")

    # Construct the objective function
    objective_function = model_question1b.setObjective(
        1.03 * sum(sl_distance_centers_landfills.loc[i, j] * xcl[i, j] for i in centers for j in landfills),
        GRB.MINIMIZE)

    # Waste collection constraints:
    # We must transport all waste away from each center
    collect_waste_constraint = model_question1b.addConstrs(
        (sum(xcl[i, j] for j in landfills) == center_info.loc[i, 'waste tonnage'] for i in centers),
        name="collect_waste")

    # We can only transport waste to landfill locations that have been built
    bibig_M_constraint = model_question1b.addConstrs(
        (xcl[i, j] <= bigM * z[j] for i in centers for j in landfills),
        name="big_M")

    # We can build at most 4 landfills
    max_num_landfills_constraint = model_question1b.addConstr(
        sum(z[j] for j in landfills) <= 4,
        name="max_num_landfills")


    # In[6]:


    model_question1b.optimize()


    # In[7]:


    built_landfills = []
    ret_str = ""
    for j in landfills:
        if z[j].x >= 0.9999:
            ret_str += "Build landfill at" + j + "\n"
            built_landfills.append(j)

    total_cost = 1.03 * sum(sl_distance_centers_landfills.loc[i,j]*xcl[i,j].x for i in centers for j in landfills)
    return ["Total weekly cost is: $ %f" % total_cost + "\n" + ret_str]


    # In[ ]:




