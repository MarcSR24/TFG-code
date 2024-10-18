import matplotlib.pyplot as plt

def plot_gap(X_values : list[int], y_values : list[float], plot_name : str, plot_title : str):
    """
    This function plots the values taking into account that there might be gaps in the data

    Parameters:
        X_values : list of integers
            The values in the X axis
        y_values : list of floats
            The values in the Y axis
        plot_name : string
            The path to where the plot will be saved
    """
    # Get the points of data where there is a gap in X_values
    splits = []
    for idx in range(1,len(X_values)):
        if int(X_values[idx-1]) + 1 != int(X_values[idx]):
            splits.append(idx)
    # Create the splits of data based on where the gaps are
    X_values_splits = []
    y_values_splits = []
    if len(splits) > 0:
        X_values_splits.append(X_values[:splits[0]])
        y_values_splits.append(y_values[:splits[0]])
        if len(splits) > 1:
            for idx in range(len(splits[:-1])):
                X_values_splits.append(X_values[splits[idx]:splits[idx+1]])
                y_values_splits.append(y_values[splits[idx]:splits[idx+1]])
        X_values_splits.append(X_values[splits[-1]:])
        y_values_splits.append(y_values[splits[-1]:])
    # Plot the data
    fig, ax = plt.subplots()
    for p,v in zip(X_values_splits,y_values_splits):
        ax.bar(p,v,color='darkred')
        ax.plot(p,v,color='#3a3a3a')
    ax.set_title(plot_title)
    ax.set_xlabel("Years")
    ax.set_ylabel("Number of repetitons")
    ax.grid(True)
    fig.savefig(plot_name)
    return fig