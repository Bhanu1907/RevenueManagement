# -*- coding: utf-8 -*-
"""
IB9EO0 - Group 16

"""

# Imports numpy package and names it np
import numpy as np

# Imports pandas package and names it pd
import pandas as pd

from pyomo.environ import *
 
file_name='WCG_DataSetV1.xlsx'

# Function to convert string to zero in the data
def stringToZero(value):
    if isinstance(value, str):
        return 0
    else:
        return value

# Reads the file
df = pd.read_excel(file_name, "WCG Data", converters={'£/Day': stringToZero},header=7, index_col=1, na_values= ['Nan'])


price_matrix = df[['£/Day','£/Day.1','£/Day.2','£/Day.3']]
demand_matrix = df[['Demand', 'Demand.1','Demand.2','Demand.3']]
return_matrix = df[['Returned','Returned.1','Returned.2','Returned.3']]

# Extracts £/day from the data and replace NaN values with zero for holiday weeks
price_np =  np.nan_to_num(price_matrix.to_numpy()[0:52,])

# Extract demands from the data and replace NaN values with zero for holiday weeks
demand_np = np.nan_to_num(demand_matrix.to_numpy()[0:52,])

# Extract return from the data
return_np = np.nan_to_num(return_matrix.to_numpy()[0:52,])

# Extracts number of weeks from the data
Week_No = df.index.to_numpy()[0:52]

# Returns from last year for 1-Week, 4-Week, 8-Week, 16-Week rental options
Return_Week1 = return_np[0:2,0]
Return_Week4 = return_np[0:5,1]
Return_Week8 = return_np[0:9,2]
Return_Week16 = return_np[0:17,3]

# Rental plans
lease_options = [1,4,8,16]

# Total number of weeks
numWeeks = len(Week_No)

# Total number of rental options
numofPlans = len(lease_options)

# Creates a blank concrete model
model = ConcreteModel()

# Creates a variable called acpt for the number of containers accepted for each rental option
model.acpt = Var(range(numWeeks),range(numofPlans), domain=NonNegativeIntegers)

# Creates a variable called inv for the number of inventories for each week
model.inv = Var(range(numWeeks), domain=NonNegativeIntegers)


# Creates the objective function rule
def model_objective(model):
 total_revenue = 0
 for j in range(numofPlans):
     sum_product=0
     for i in range(numWeeks):
         sum_product += price_np[i,j]*model.acpt[i,j] 
     total_revenue += sum_product*lease_options[j]*7
 return(total_revenue)

# Adds the objective function to the model using the obj_rule     
model.obj = Objective(rule=model_objective, sense=maximize)


# Constraints

# Demand constraint
def demand_rule(model,j,i):
    return model.acpt[i,j] <= demand_np[i,j]

# Adding the constraint to the model
model.demand_constr = Constraint(range(numofPlans),range(numWeeks),rule=demand_rule)
 


# Inventory constraint
def cal_inv_rule(model, i):
    return (model.inv[i-1] - sum(model.acpt[i-1, j] for j in range(numofPlans)) +
            sum((Return_Week1[i] if i <= 1 and j == 0 else
                 Return_Week4[i] if i <= 4 and j == 1 else
                 Return_Week8[i] if i <= 8 and j == 2 else
                 Return_Week16[i] if i <= 16 and j == 3 else
                 model.acpt[i, j]) for j in range(numofPlans)) == model.inv[i])

# Adding the constraint to the model
model.cal_inv_constr = Constraint(range(1,numWeeks), rule=cal_inv_rule)


# Total accepted demands till particular week should not exceed 300
def tot_accepted_rule(model, i):
    tot_accepted = (sum(model.acpt[i,j] for j in range(numofPlans)) 
            +(sum(model.acpt[k, 1] for k in range(max(i-3, 0), i))
            +sum(model.acpt[k, 2] for k in range(max(i-7, 0), i))
            +sum(model.acpt[k, 3] for k in range(max(i-15, 0), i))))
    return (tot_accepted<=300)

# Adding the constraint to the model
model.tot_accepted_constr = Constraint(range(numWeeks), rule=tot_accepted_rule) 


# Initial inventory
def ini_inv_rule(model):
    return model.inv[0] == 77
# Adding the constraint to the model
model.ini_inv = Constraint(rule=ini_inv_rule)


# Prints the model
model.pprint()

# Selecting the solver
solver = SolverFactory('glpk')
# Solving the model
results = solver.solve(model)

# Results

# Check if the solution is optimal and display the results
if (results.solver.status == SolverStatus.ok) and (results.solver.termination_condition == TerminationCondition.optimal):
    for i in range(numWeeks):
      for j in range(numofPlans):
        print('Accepted demands for containers on week no',i+1,'and',lease_options[j],'Week rental option is', model.acpt[i,j](),'for the price ',price_np[i,j],'pounds' )
    print('')
    print('Maximum Revenue is', round(model.obj(),2)/1000, 'Pounds (x1000)')
    print('')
else:
    print("Solve failed.") 
    
   
# Calculating total accepted number of demands for each rental option    
def total_accepted():
  for j in range(numofPlans):
     sum = 0
     for i in range(numWeeks):
        sum += model.acpt[i,j]() 
     result = sum
     print('Total accepted demands for',lease_options[j], 'Week rental is', sum)

total_accepted()


# Inventory for each week
def inventory():
    print('')
    for i in range(numWeeks):
        print('Inventory for week', i+1 ,'is ', model.inv[i]())
        
inventory()






 