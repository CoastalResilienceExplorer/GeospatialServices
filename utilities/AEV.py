import numpy as np
from collections import OrderedDict

def calculate_AEV(rp , values): 
    
    rp      = np.array(rp)
    values  = np.array(values)
    
    # probability 
    probability = 1.0 / rp 
        
    #add rp = 1
    if any(probability==1)==False: 
        x = probability.tolist()
        x.append(1)
        y = values.tolist()
        y.append(0) # loss 0 for annual flood 
        
        probability = np.array(x) 
        values      = np.array(y)
    
    # sort
    ind = np.argsort(probability)
    ind[::-1]
    probability = probability[ind[::-1]]
    values      = values[ind[::-1]]
    
    #fig = plt.figure(), ax = plt.axes(), ax.plot(rp,loss)
    
    # calculate Annual Expected Value 
    DX  = probability[0:-1] - probability[1:]
    DY  = values[0:-1] +  values[1:]
    AEV = sum(DX*DY)/2
    #DX = head(probability,-1)-tail(probability,-1) 
    # DY = head(values,-1)+tail(values,-1)
    
    return AEV 