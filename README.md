# AusCycling Team Pursuit
## Running the Grapher:
Once you have Gurobi set up on your computer, run ```python backend.py```

The command will give you a link to your local server that should now be running: http://127.0.0.1:8000/

Upload the corresponding Excel files to the application, and wait for the code to output the optimal solution (and its corresponding graphs)

### More Output:
Once the application outputs the results, there are extended results in the file ```gurobi_implementation/results.csv```

## Example Excel Files:
Included in the repo are template files for the riders' physiology and power curves (the files are titled ```physiology_template.xlsx``` and ```power_curve_template.xlsx```)


## Toggling Optimizer:
The application relies on the python file ```gurobi_implementation/optimizer.py```, which mimics its Jupyter Notebook counterpart ```optimizer.ipynb```.

Users can run the optimization on the Jupyter Notebook file or through the local server application.

### Changing Times:
The array ```half_lap_times``` (which users can search for using computer commands) iterates through a finite number of reasonable half lap times.

Add or remove times to improve range/speed of optimizer

### Changing Interval Number:
Similarly, edit the variables ```init_num_intervals``` and ```num_intervals_to_try``` to change the range of intervals tested. 

The optimizer tests the intervals from __init_num_intervals__ to __init_num_intervals + num_intervals_to_try - 1__.