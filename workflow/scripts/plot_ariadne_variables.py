import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

def ariadne_subplot(
    df, ax, title, 
    select_regex="", drop_regex="", stacked=True,
):
    df = df.T.copy()
    if select_regex:
        df = df.filter(
            regex=select_regex,
        )
    if drop_regex:
        df = df.filter(
            regex=drop_regex,
        )
    # Check that all values have the same Unit
    assert df.columns.unique(level="Unit").size == 1

    # Simplify variable names
    df.columns = pd.Index(
        map(
            lambda x: x[0][(x[0].find("|") + 1):], 
            df.columns,
        ),
        name=df.columns.names[0],
    )

    return df.plot.area(ax=ax, title=title, legend=False, stacked=stacked)



def side_by_side_plot(
        df, dfhybrid, title, savepath,
        rshift=1.25, **kwargs
    ):
    idx = df.index.intersection(dfhybrid.index)
    df = df.loc[idx]
    dfhybrid = dfhybrid.loc[idx]

    fig, axes = plt.subplots(ncols=2, sharey=True)
    ax = ariadne_subplot(df, axes[0], "PyPSA-Eur", **kwargs)
    ax2 = ariadne_subplot(dfhybrid, axes[1], "REMIND-EU v1.1", **kwargs)
    
    handles, labels = ax.get_legend_handles_labels()
    labels2 = ax2.get_legend_handles_labels()[1]
    assert labels == labels2

    fig.legend(
        reversed(handles), 
        reversed(labels), 
        bbox_to_anchor=(rshift,0.9)
    )
    fig.suptitle(title)
    title = title.replace(" ", "_")
    fig.savefig(savepath, bbox_inches="tight")
    return fig 

def within_plot(df, df2, 
                title, savepath, 
                select_regex="", drop_regex="",
                write_sum = False,
                unit = "EUR_2020/GJ", **kwargs
                ):

    df = df.T.copy()
    if select_regex:
        df = df.filter(
            regex=select_regex,
        )
    if drop_regex:
        df = df.filter(
            regex=drop_regex,
        )
    
    n = df.shape[1]
    if n == 0:
        print(f"Warning! Apparently the variables required for this plot (({title}) are missing.")
        fig = plt.figure()
        plt.title(f"Warning! Apparently the variables required for this plot ({title}) are missing.")
        fig.savefig(savepath, bbox_inches="tight")
        return fig
    rows = n // 2 + n % 2 

    fig, axes = plt.subplots(rows, 2, figsize=(10, 5 * rows))
    axes = axes.flatten()

    for i, var in enumerate(df.columns.get_level_values("Variable")):

        axes[i].plot(df.xs(var, axis=1, level=0), label="PyPSA-Eur")
        if var in df2.index.get_level_values("Variable"):
            axes[i].plot(df2.T.xs(var, axis=1, level=0), label="REMIND-EU")   
        axes[i].set_title(var)
        axes[i].legend()

        if write_sum:
            sum_df1 = round(df.xs(var, axis=1, level=0).sum().values.item(), 2)
            if var in df2.index.get_level_values("Variable"):
                sum_df2 = round(df2.T.xs(var, axis=1, level=0).sum().values.item(), 2)
            else:
                sum_df2 = np.nan
            # Annotate plot with the sum of variables
            sum_text = f"Sum: \nPyPSA-Eur = {sum_df1},\nREMIND-EU = {sum_df2}"
            axes[i].annotate(sum_text, xy=(0, 1), xycoords='axes fraction', fontsize=12,
                        xytext=(5, -5), textcoords='offset points', ha='left', va='top')



    # Remove the last subplot if there's an odd number of plots
    if n % 2 != 0:
        fig.delaxes(axes[-1])

    plt.suptitle(f"{title} in ({unit})", fontsize="xx-large", y=1.0)
    plt.tight_layout()
    plt.close()
    fig.savefig(savepath, bbox_inches="tight")

    return fig 

def elec_val_plot(df, savepath):
    # electricity validation for 2020
    elec_capacities = pd.DataFrame(index=["ror", "hydro", "battery", "biomass", "nuclear", "lignite", "coal", "oil", "gas", "wind_onshore", "wind_offshore", "solar"])
    elec_generation = pd.DataFrame(index=["ror", "hydro", "battery", "biomass", "nuclear", "lignite", "coal", "oil", "gas", "wind", "solar"])

    elec_capacities["real"] = [4.94, 9.69, 2.4, 8.72, 8.11, 20.86, 23.74, 4.86, 32.54, 54.25, 7.86, 54.36] # https://energy-charts.info/charts/installed_power/chart.htm?l=en&c=DE&year=2020
    elec_generation["real"] = [np.nan, 18.7, np.nan, 45, 64, 91, 43, 4.7, 95, 132, 50] # https://www.destatis.de/DE/Themen/Branchen-Unternehmen/Energie/Erzeugung/Tabellen/bruttostromerzeugung.html
    elec_capacities["pypsa"] = [
        0,
        df.loc[("Capacity|Electricity|Hydro", "GW"), "2020"],
        0,
        df.loc[("Capacity|Electricity|Biomass", "GW"), "2020"],
        df.loc[("Capacity|Electricity|Nuclear", "GW"), "2020"],
        df.loc[("Capacity|Electricity|Coal|Lignite", "GW"), "2020"],
        df.loc[("Capacity|Electricity|Coal|Hard Coal", "GW"), "2020"],
        df.loc[("Capacity|Electricity|Oil", "GW"), "2020"],
        df.loc[("Capacity|Electricity|Gas", "GW"), "2020"],
        df.loc[("Capacity|Electricity|Wind|Onshore", "GW"), "2020"],
        df.loc[("Capacity|Electricity|Wind|Offshore", "GW"), "2020"],
        df.loc[("Capacity|Electricity|Solar", "GW"), "2020"],
    ]

    elec_generation["pypsa"] = [
        0,
        df.loc[("Secondary Energy|Electricity|Hydro", "PJ/yr"), "2020"] / 3.6,
        0,
        df.loc[("Secondary Energy|Electricity|Biomass", "PJ/yr"), "2020"] / 3.6,
        df.loc[("Secondary Energy|Electricity|Nuclear", "PJ/yr"), "2020"] / 3.6,
        df.loc[("Secondary Energy|Electricity|Coal|Lignite", "PJ/yr"), "2020"] / 3.6,
        df.loc[("Secondary Energy|Electricity|Coal|Hard Coal", "PJ/yr"), "2020"] / 3.6,
        df.loc[("Secondary Energy|Electricity|Oil", "PJ/yr"), "2020"] / 3.6,
        df.loc[("Secondary Energy|Electricity|Gas", "PJ/yr"), "2020"] / 3.6,
        df.loc[("Secondary Energy|Electricity|Wind", "PJ/yr"), "2020"] / 3.6,
        df.loc[("Secondary Energy|Electricity|Solar", "PJ/yr"), "2020"] / 3.6,
    ]

    fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    elec_capacities.plot(kind="bar", ax=axes[0])
    axes[0].set_ylabel("GW")
    axes[0].set_title("Installed Capacities Germany 2020")

    elec_generation.plot(kind="bar", ax=axes[1])
    axes[1].set_ylabel("TWh")
    axes[1].set_title("Electricity Generation Germany 2020")

    plt.tight_layout()
    plt.close()
    fig.savefig(savepath, bbox_inches="tight")

    return fig


if __name__ == "__main__":
    if "snakemake" not in globals():
        import os
        import sys

        path = "../submodules/pypsa-eur/scripts"
        sys.path.insert(0, os.path.abspath(path))
        from _helpers import mock_snakemake

        snakemake = mock_snakemake(
            "plot_ariadne_variables",
            simpl="",
            clusters=22,
            opts="",
            ll="v1.2",
            sector_opts="None",
            planning_horizons="2050",
            run="KN2045_Bal_v4"
        )

    df = pd.read_excel(
        snakemake.input.exported_variables_full,
        index_col=list(range(5)),
        #index_col=["Model", "Scenario", "Region", "Variable", "Unit"],
        sheet_name="data"
    ).groupby(["Variable","Unit"], dropna=False).sum()

    df.columns = df.columns.astype(str)
    leitmodell="REMIND-EU v1.1"

    dfremind = pd.read_csv(
        snakemake.input.ariadne_database,
        index_col=["model", "scenario", "region", "variable", "unit"]
    ).loc[
        leitmodell, snakemake.params.iiasa_scenario, "Deutschland"
    ][df.columns]
    dfremind.index.names = df.index.names

    side_by_side_plot(
        df,
        dfremind,
        "Primary Energy in PJ_yr",
        savepath=snakemake.output.primary_energy,
        select_regex="Primary Energy\|[^|]*$",
        drop_regex="^(?!.*(Fossil|Price)).+"
    )

    side_by_side_plot(
        df,
        dfremind,
        "Detailed Primary Energy in PJ_yr",
        savepath=snakemake.output.primary_energy_detailed,
        select_regex="Primary Energy\|[^|]*\|[^|]*$",
        drop_regex="^(?!.*(CCS|Price)).+"
    )

    side_by_side_plot(
        df,
        dfremind,
        "Secondary Energy in PJ_yr",
        savepath=snakemake.output.secondary_energy,
        select_regex="Secondary Energy\|[^|]*$",
        drop_regex="^(?!.*(Price)).+"

    )

    side_by_side_plot(
        df,
        dfremind,
        "Detailed Secondary Energy in PJ_yr",
        savepath=snakemake.output.secondary_energy_detailed,
        # Secondary Energy|Something|Something (exactly two pipes)
        select_regex="Secondary Energy\|[^|]*\|[^|]*$",
        # Not ending in Fossil or Renewables (i.e., categories)
        drop_regex="^(?!.*(Fossil|Renewables|Losses|Price)).+"
    )

    side_by_side_plot(
        df,
        dfremind,
        "Final Energy in PJ_yr",
        savepath=snakemake.output.final_energy,
        select_regex="Final Energy\|[^|]*$",
        rshift = 1.45,
        drop_regex="^(?!.*(Price|Non-Energy Use)).+"
    )

    side_by_side_plot(
        df,
        dfremind,
        "Detailed Final Energy in PJ_yr",
        savepath=snakemake.output.final_energy_detailed,
        select_regex="Final Energy\|[^|]*\|[^|]*$",
        rshift = 1.7,
        drop_regex="^(?!.*(Price|\|Solids\||Non-Energy Use\|)).+"
    )

    side_by_side_plot(
        df,
        dfremind,
        "Capacity in GW",
        savepath=snakemake.output.capacity,
        select_regex="Capacity\|[^|]*$",
    )

    side_by_side_plot(
        df,
        dfremind,
        "Detailed Capacity in GW",
        savepath=snakemake.output.capacity_detailed,
        select_regex="Capacity\|[^|]*\|[^|]*$",
        drop_regex="^(?!.*(Reservoir|Converter)).+"
    )

    side_by_side_plot(
        df,
        dfremind,
        "Detailed Demand Emissions in Mt",
        savepath=snakemake.output.energy_demand_emissions,
        select_regex="Emissions\|CO2\|Energy\|Demand\|[^|]*$",
        stacked=False,
    )

    side_by_side_plot(
        df,
        dfremind,
        "Detailed Supply Emissions in Mt",
        savepath=snakemake.output.energy_supply_emissions,
        select_regex="Emissions\|CO2\|Energy\|Supply\|[^|]*$",
        stacked=False,

        drop_regex="^(?!.*(and)).+"
    )

    side_by_side_plot(
        df,
        dfremind,
        "Detailed Emissions in Mt",
        savepath=snakemake.output.co2_emissions,
        select_regex="Emissions\|CO2\|[^|]*$",
        stacked=False,
        #drop_regex="^(?!.*(and)).+"
    )

    within_plot(
        df, 
        dfremind, 
        title = "Price|Primary Energy", 
        savepath=snakemake.output.primary_energy_price,
        select_regex="Price\|Primary Energy\|[^|]*$"
    )
    
    within_plot(
        df[df.index.get_level_values("Variable").str.startswith("Price|Secondary Energy")], 
        dfremind, 
        title = "Price|Secondary Energy", 
        savepath=snakemake.output.secondary_energy_price,
    )

    # within_plot(
    #     df[df.index.get_level_values("Variable").str.startswith("Price|Final Energy|Residential")], 
    #     dfremind, 
    #     title = "Price|Final Energy|Residential", 
    #     savepath=snakemake.output.final_energy_residential_price,
    #     #select_regex="Price\|Final Energy\|Residential\|[^|]*$"
    # )

    within_plot(
        df[df.index.get_level_values("Variable").str.startswith("Price|Final Energy|Industry")], 
        dfremind, 
        title = "Price|Final Energy|Industry", 
        savepath=snakemake.output.final_energy_industry_price,
        #select_regex="Price\|Final Energy\|Industry\|[^|]*$"
    )

    within_plot(
        df[df.index.get_level_values("Variable").str.startswith("Price|Final Energy|Transportation")], 
        dfremind, 
        title = "Price|Final Energy|Transportation", 
        savepath=snakemake.output.final_energy_transportation_price,
        #select_regex="Price\|Final Energy\|Industry\|[^|]*$"
    )

    within_plot(
        df[df.index.get_level_values("Variable").str.startswith("Price|Final Energy|Residential and Commercial")], 
        dfremind, 
        title = "Price|Final Energy|Residential and Commercial", 
        savepath=snakemake.output.final_energy_residential_commercial_price,
        #select_regex="Price\|Final Energy\|Industry\|[^|]*$"
    )

    within_plot(
        df[df.index.get_level_values("Variable").str.startswith('Price')], 
        dfremind, 
        title = "All prices", 
        savepath=snakemake.output.all_prices,
    )

    within_plot(
        df[df.index.get_level_values("Variable").str.startswith('Price|Carbon')], 
        dfremind, 
        title = "Price of carbon", 
        savepath=snakemake.output.policy_carbon,
        unit="EUR/tCO2",
    )

    within_plot(
        df[df.index.get_level_values("Variable").str.startswith('Investment|Energy Supply')], 
        dfremind, 
        title = "Investment in Energy Supply", 
        savepath=snakemake.output.investment_energy_supply ,
        unit="billion EUR",
        write_sum = True,
    )

    elec_val_plot(df, savepath=snakemake.output.elec_val_2020)

